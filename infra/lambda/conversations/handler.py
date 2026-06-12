"""Conversations API Lambda.

Routes (HTTP API payload v2, Cognito JWT default authorizer in front):
  GET /v1/conversations                       -> list this user's conversations
  PUT /v1/conversations/{sessionId}           -> upsert a conversation name
  GET /v1/conversations/{sessionId}/messages  -> replay messages from AgentCore Memory

The actor is ALWAYS the Cognito ``sub`` claim from the JWT validated by API
Gateway — never a path/query/body value — so users can only see their own data.
"""

import json
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key

MAX_NAME_LENGTH = 60
ROLE_MAP = {"USER": "user", "ASSISTANT": "assistant"}

_table = None
_agentcore = None


def _get_table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["CONVERSATION_TABLE"])
    return _table


def _get_agentcore():
    global _agentcore
    if _agentcore is None:
        _agentcore = boto3.client("bedrock-agentcore")
    return _agentcore


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _actor_id(event):
    """Actor identity comes exclusively from the JWT claims set by the API
    Gateway authorizer. Returns None if absent (request not authenticated)."""
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )
    sub = claims.get("sub")
    return sub or None


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")

    # CORS preflight: the unauthorized OPTIONS /{proxy+} route lands here when
    # API Gateway doesn't answer the preflight itself. API Gateway appends the
    # configured CORS headers to this response.
    if method == "OPTIONS":
        return {"statusCode": 204, "headers": {}, "body": ""}

    actor_id = _actor_id(event)
    if not actor_id:
        return _response(401, {"error": "unauthorized"})

    route_key = event.get("routeKey", "")
    session_id = event.get("pathParameters", {}).get("sessionId") if event.get("pathParameters") else None

    if route_key == "GET /v1/conversations":
        return list_conversations(actor_id)
    if route_key == "PUT /v1/conversations/{sessionId}" and session_id:
        return put_conversation(actor_id, session_id, event.get("body"))
    if route_key == "GET /v1/conversations/{sessionId}/messages" and session_id:
        return list_messages(actor_id, session_id)

    return _response(404, {"error": f"no route for {method} {event.get('rawPath', '')}"})


def list_conversations(actor_id):
    table = _get_table()
    items = []
    query_kwargs = {"KeyConditionExpression": Key("actor_id").eq(actor_id)}
    while True:
        page = table.query(**query_kwargs)
        items.extend(page.get("Items", []))
        last_key = page.get("LastEvaluatedKey")
        if not last_key:
            break
        query_kwargs["ExclusiveStartKey"] = last_key

    items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    conversations = [
        {
            "session_id": item.get("session_id"),
            "conversation_name": item.get("conversation_name"),
            "created_at": item.get("created_at"),
        }
        for item in items
    ]
    return _response(200, {"conversations": conversations})


def put_conversation(actor_id, session_id, raw_body):
    try:
        body = json.loads(raw_body or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "invalid JSON body"})

    name = body.get("conversation_name")
    if not isinstance(name, str) or not name.strip():
        return _response(400, {"error": "conversation_name is required"})
    name = name.strip()[:MAX_NAME_LENGTH]

    table = _get_table()

    # Preserve created_at on rename: read the existing item (Query on the full
    # key — the role only has dynamodb:Query + dynamodb:PutItem), then put.
    existing = table.query(
        KeyConditionExpression=Key("actor_id").eq(actor_id) & Key("session_id").eq(session_id)
    ).get("Items", [])
    created_at = (
        existing[0].get("created_at")
        if existing
        else datetime.now(timezone.utc).isoformat()
    )

    item = {
        "actor_id": actor_id,
        "session_id": session_id,
        "conversation_name": name,
        "created_at": created_at,
    }
    table.put_item(Item=item)
    return _response(
        200,
        {"session_id": session_id, "conversation_name": name, "created_at": created_at},
    )


def list_messages(actor_id, session_id):
    client = _get_agentcore()
    memory_id = os.environ["AGENTCORE_MEMORY_ID"]

    events = []
    kwargs = {
        "memoryId": memory_id,
        "actorId": actor_id,
        "sessionId": session_id,
        "includePayloads": True,
    }
    while True:
        page = client.list_events(**kwargs)
        events.extend(page.get("events", []))
        next_token = page.get("nextToken")
        if not next_token:
            break
        kwargs["nextToken"] = next_token

    # list_events returns newest-first; sort events chronologically ascending,
    # keeping payload order within each event.
    def _event_ts(evt):
        ts = evt.get("eventTimestamp")
        return ts.isoformat() if isinstance(ts, datetime) else str(ts or "")

    events.sort(key=_event_ts)

    messages = []
    for evt in events:
        timestamp = _event_ts(evt)
        for payload in evt.get("payload", []):
            conversational = payload.get("conversational")
            if not conversational:
                continue
            role = conversational.get("role", "")
            text = conversational.get("content", {}).get("text", "")
            messages.append(
                {
                    "role": ROLE_MAP.get(role, role.lower()),
                    "content": text,
                    "timestamp": timestamp,
                }
            )

    return _response(200, {"messages": messages})
