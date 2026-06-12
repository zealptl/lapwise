"""Unit tests for the conversations Lambda: route dispatch, actor isolation
(actor only ever comes from JWT claims), and conversational payload mapping.

All boto3 clients are mocked — tests run offline.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from boto3.dynamodb.conditions import Key

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import handler  # noqa: E402

SUB = "11111111-2222-3333-4444-555555555555"
SESSION = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def make_event(method, route_key, raw_path, sub=SUB, session_id=None, body=None, query=None):
    event = {
        "routeKey": route_key,
        "rawPath": raw_path,
        "requestContext": {
            "http": {"method": method},
        },
    }
    if sub is not None:
        event["requestContext"]["authorizer"] = {"jwt": {"claims": {"sub": sub}}}
    if session_id is not None:
        event["pathParameters"] = {"sessionId": session_id}
    if body is not None:
        event["body"] = json.dumps(body)
    if query is not None:
        event["queryStringParameters"] = query
    return event


@pytest.fixture
def table(monkeypatch):
    mock_table = MagicMock()
    mock_table.query.return_value = {"Items": []}
    monkeypatch.setattr(handler, "_get_table", lambda: mock_table)
    return mock_table


@pytest.fixture
def agentcore(monkeypatch):
    mock_client = MagicMock()
    mock_client.list_events.return_value = {"events": []}
    monkeypatch.setattr(handler, "_get_agentcore", lambda: mock_client)
    monkeypatch.setenv("AGENTCORE_MEMORY_ID", "LapwiseF1Agent_LapwiseMemory-BpEoUO9hnK")
    return mock_client


def body_of(response):
    return json.loads(response["body"])


# ── Route dispatch ────────────────────────────────────────────────────────────


def test_options_preflight_returns_204_without_auth(table):
    event = make_event("OPTIONS", "OPTIONS /{proxy+}", "/v1/conversations", sub=None)
    assert handler.handler(event, None)["statusCode"] == 204
    table.query.assert_not_called()


def test_unknown_route_returns_404(table):
    event = make_event("DELETE", "DELETE /v1/conversations", "/v1/conversations")
    assert handler.handler(event, None)["statusCode"] == 404


def test_get_conversations_dispatches(table):
    event = make_event("GET", "GET /v1/conversations", "/v1/conversations")
    response = handler.handler(event, None)
    assert response["statusCode"] == 200
    assert "conversations" in body_of(response)


def test_put_conversation_dispatches(table):
    event = make_event(
        "PUT",
        "PUT /v1/conversations/{sessionId}",
        f"/v1/conversations/{SESSION}",
        session_id=SESSION,
        body={"conversation_name": "Monza strategy"},
    )
    assert handler.handler(event, None)["statusCode"] == 200


def test_get_messages_dispatches(agentcore):
    event = make_event(
        "GET",
        "GET /v1/conversations/{sessionId}/messages",
        f"/v1/conversations/{SESSION}/messages",
        session_id=SESSION,
    )
    response = handler.handler(event, None)
    assert response["statusCode"] == 200
    assert body_of(response) == {"messages": []}


# ── Actor isolation: actor_id only ever comes from JWT claims ────────────────


def test_missing_jwt_sub_returns_401(table):
    event = make_event("GET", "GET /v1/conversations", "/v1/conversations", sub=None)
    assert handler.handler(event, None)["statusCode"] == 401
    table.query.assert_not_called()


def test_empty_jwt_sub_returns_401(table):
    event = make_event("GET", "GET /v1/conversations", "/v1/conversations", sub="")
    assert handler.handler(event, None)["statusCode"] == 401


def test_list_queries_by_jwt_sub_ignoring_query_params(table):
    event = make_event(
        "GET",
        "GET /v1/conversations",
        "/v1/conversations",
        query={"actor_id": "someone-else"},
    )
    handler.handler(event, None)
    kwargs = table.query.call_args.kwargs
    assert kwargs["KeyConditionExpression"] == Key("actor_id").eq(SUB)


def test_put_uses_jwt_sub_ignoring_body_actor_id(table):
    event = make_event(
        "PUT",
        "PUT /v1/conversations/{sessionId}",
        f"/v1/conversations/{SESSION}",
        session_id=SESSION,
        body={"conversation_name": "Quali recap", "actor_id": "someone-else"},
    )
    handler.handler(event, None)
    item = table.put_item.call_args.kwargs["Item"]
    assert item["actor_id"] == SUB
    assert item["session_id"] == SESSION


def test_messages_uses_jwt_sub_as_actor(agentcore):
    event = make_event(
        "GET",
        "GET /v1/conversations/{sessionId}/messages",
        f"/v1/conversations/{SESSION}/messages",
        session_id=SESSION,
        query={"actorId": "someone-else"},
    )
    handler.handler(event, None)
    kwargs = agentcore.list_events.call_args.kwargs
    assert kwargs["actorId"] == SUB
    assert kwargs["sessionId"] == SESSION
    assert kwargs["includePayloads"] is True


# ── GET /v1/conversations ─────────────────────────────────────────────────────


def test_list_sorts_by_created_at_descending(table):
    table.query.return_value = {
        "Items": [
            {"actor_id": SUB, "session_id": "s1", "conversation_name": "old", "created_at": "2026-01-01T00:00:00+00:00"},
            {"actor_id": SUB, "session_id": "s2", "conversation_name": "new", "created_at": "2026-06-01T00:00:00+00:00"},
            {"actor_id": SUB, "session_id": "s3", "conversation_name": "mid", "created_at": "2026-03-01T00:00:00+00:00"},
        ]
    }
    event = make_event("GET", "GET /v1/conversations", "/v1/conversations")
    conversations = body_of(handler.handler(event, None))["conversations"]
    assert [c["session_id"] for c in conversations] == ["s2", "s3", "s1"]
    assert set(conversations[0]) == {"session_id", "conversation_name", "created_at"}


def test_list_paginates(table):
    table.query.side_effect = [
        {"Items": [{"session_id": "s1", "conversation_name": "a", "created_at": "2026-01-01"}],
         "LastEvaluatedKey": {"actor_id": SUB, "session_id": "s1"}},
        {"Items": [{"session_id": "s2", "conversation_name": "b", "created_at": "2026-02-01"}]},
    ]
    event = make_event("GET", "GET /v1/conversations", "/v1/conversations")
    conversations = body_of(handler.handler(event, None))["conversations"]
    assert len(conversations) == 2
    assert table.query.call_count == 2
    assert table.query.call_args_list[1].kwargs["ExclusiveStartKey"] == {
        "actor_id": SUB,
        "session_id": "s1",
    }


# ── PUT /v1/conversations/{sessionId} ─────────────────────────────────────────


def test_put_truncates_name_to_60_chars(table):
    event = make_event(
        "PUT",
        "PUT /v1/conversations/{sessionId}",
        f"/v1/conversations/{SESSION}",
        session_id=SESSION,
        body={"conversation_name": "x" * 200},
    )
    response = handler.handler(event, None)
    item = table.put_item.call_args.kwargs["Item"]
    assert item["conversation_name"] == "x" * 60
    assert body_of(response)["conversation_name"] == "x" * 60


def test_put_create_sets_created_at(table):
    table.query.return_value = {"Items": []}
    event = make_event(
        "PUT",
        "PUT /v1/conversations/{sessionId}",
        f"/v1/conversations/{SESSION}",
        session_id=SESSION,
        body={"conversation_name": "New chat"},
    )
    response = handler.handler(event, None)
    item = table.put_item.call_args.kwargs["Item"]
    assert item["created_at"]  # ISO 8601 now
    datetime.fromisoformat(item["created_at"])
    assert body_of(response)["created_at"] == item["created_at"]


def test_put_rename_preserves_created_at(table):
    original = "2026-01-15T12:00:00+00:00"
    table.query.return_value = {
        "Items": [{"actor_id": SUB, "session_id": SESSION, "conversation_name": "old", "created_at": original}]
    }
    event = make_event(
        "PUT",
        "PUT /v1/conversations/{sessionId}",
        f"/v1/conversations/{SESSION}",
        session_id=SESSION,
        body={"conversation_name": "renamed"},
    )
    handler.handler(event, None)
    item = table.put_item.call_args.kwargs["Item"]
    assert item["created_at"] == original
    assert item["conversation_name"] == "renamed"


def test_put_rejects_missing_name(table):
    event = make_event(
        "PUT",
        "PUT /v1/conversations/{sessionId}",
        f"/v1/conversations/{SESSION}",
        session_id=SESSION,
        body={},
    )
    assert handler.handler(event, None)["statusCode"] == 400
    table.put_item.assert_not_called()


def test_put_rejects_invalid_json(table):
    event = make_event(
        "PUT",
        "PUT /v1/conversations/{sessionId}",
        f"/v1/conversations/{SESSION}",
        session_id=SESSION,
    )
    event["body"] = "{not json"
    assert handler.handler(event, None)["statusCode"] == 400


# ── GET /v1/conversations/{sessionId}/messages — payload mapping ─────────────


def _agent_event(ts, *turns):
    return {
        "eventTimestamp": ts,
        "payload": [
            {"conversational": {"content": {"text": text}, "role": role}}
            for text, role in turns
        ],
    }


def test_messages_maps_roles_and_sorts_ascending(agentcore):
    t1 = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 6, 1, 10, 1, 0, tzinfo=timezone.utc)
    # list_events returns newest-first
    agentcore.list_events.return_value = {
        "events": [
            _agent_event(t2, ("Verstappen won.", "ASSISTANT")),
            _agent_event(t1, ("Who won Monza?", "USER"), ("Checking...", "ASSISTANT")),
        ]
    }
    event = make_event(
        "GET",
        "GET /v1/conversations/{sessionId}/messages",
        f"/v1/conversations/{SESSION}/messages",
        session_id=SESSION,
    )
    messages = body_of(handler.handler(event, None))["messages"]
    assert messages == [
        {"role": "user", "content": "Who won Monza?", "timestamp": t1.isoformat()},
        {"role": "assistant", "content": "Checking...", "timestamp": t1.isoformat()},
        {"role": "assistant", "content": "Verstappen won.", "timestamp": t2.isoformat()},
    ]


def test_messages_skips_non_conversational_payloads(agentcore):
    ts = datetime(2026, 6, 1, tzinfo=timezone.utc)
    agentcore.list_events.return_value = {
        "events": [
            {
                "eventTimestamp": ts,
                "payload": [
                    {"blob": "opaque"},
                    {"conversational": {"content": {"text": "hi"}, "role": "USER"}},
                ],
            }
        ]
    }
    event = make_event(
        "GET",
        "GET /v1/conversations/{sessionId}/messages",
        f"/v1/conversations/{SESSION}/messages",
        session_id=SESSION,
    )
    messages = body_of(handler.handler(event, None))["messages"]
    assert messages == [{"role": "user", "content": "hi", "timestamp": ts.isoformat()}]


def test_messages_paginates_with_next_token(agentcore):
    t1 = datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 6, 1, 9, 5, 0, tzinfo=timezone.utc)
    agentcore.list_events.side_effect = [
        {"events": [_agent_event(t2, ("second", "USER"))], "nextToken": "tok"},
        {"events": [_agent_event(t1, ("first", "USER"))]},
    ]
    event = make_event(
        "GET",
        "GET /v1/conversations/{sessionId}/messages",
        f"/v1/conversations/{SESSION}/messages",
        session_id=SESSION,
    )
    messages = body_of(handler.handler(event, None))["messages"]
    assert [m["content"] for m in messages] == ["first", "second"]
    assert agentcore.list_events.call_count == 2
    assert agentcore.list_events.call_args_list[1].kwargs["nextToken"] == "tok"
