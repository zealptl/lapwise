"""LapwiseF1Agent — GoogleADK agent for F1 Fantasy recommendations on BedrockAgentCore."""

import json
import logging
import os
import uuid

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import preload_memory

from cognito import CognitoTokenCache
from memory import AgentCoreMemoryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEMORY_ID = os.getenv("MEMORY_ID")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
GATEWAY_URL = os.getenv("AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL")

SYSTEM_PROMPT = """You are LapwiseF1Agent, an expert F1 Fantasy advisor powered by historical
Lapwise race data.

## Scoring Priority (highest to lowest)
1. DNF avoidance — a DNF scores 0 points; prioritise drivers and constructors with low DNF rates
2. Positions gained — points awarded for each place gained from grid to finish
3. Constructor pit stop reliability — fast, consistent pit stops directly contribute constructor points
4. Fastest lap bonus — significant points multiplier; favour drivers with historical fastest-lap frequency
5. Overtake count — points per overtake; circuits with high overtake rates amplify this
6. Qualifying performance — strong qualifiers start higher and gain fewer positions but score qualifying points
7. Boost pick multiplier — your designated boost driver scores 2× points; maximise this pick's expected score

## Budget constraint
All recommended teams must stay within £100M total (5 drivers + 1 constructor).
Always show the total cost breakdown.

## Output format
Always produce exactly three scenarios:

### Best team
Maximise expected points within budget. Cite the data signals that justify each pick.

### Value picks
2–3 under-priced drivers (< £10M) with strong data signals relative to their price.
Explain the data evidence for each.

### Risk-tolerant
Higher-variance picks with meaningful upside. Acknowledge the risk and the data signal.

## Boost pick guidance
Recommend the driver with the strongest combination of:
- Low DNF rate at this circuit
- High positions-gained average
- Fastest-lap historical frequency > 10%

## Transparency
Always state which Lapwise endpoints were queried and summarise the key data findings
before making recommendations. If data is unavailable for a circuit/year, say so explicitly.
"""


def _load_gateway_toolset():
    """Return an MCPToolset connected to AgentCore Gateway, or [] in dev mode."""
    if not GATEWAY_URL:
        logger.warning(
            "AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL not set — skipping gateway tools (dev mode)"
        )
        return []
    logger.info("Loading MCPToolset from gateway: %s", GATEWAY_URL)
    try:
        from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
        from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

        token = _token_cache.get_token()
        logger.info("Gateway token acquired: %s", "yes" if token else "NO TOKEN — connecting without auth")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        toolset = MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=GATEWAY_URL,
                headers=headers,
            )
        )
        logger.info("MCPToolset created successfully for gateway: %s", GATEWAY_URL)
        return [toolset]
    except Exception:
        logger.warning("Failed to load gateway toolset", exc_info=True)
        return []


def save_user_preference(preference: str) -> str:
    """Save an F1 Fantasy preference to long-term memory for future sessions.

    Call this when the user expresses a persistent preference (e.g. budget strategy,
    favourite drivers, risk tolerance). The preference is persisted via the session-end
    memory callback and available in future conversations.
    """
    if not MEMORY_ID:
        return "Memory not available in dev mode — preference noted for this session only."
    return f"Preference noted and will be saved at session end: {preference}"


async def persist_session_callback(callback_context) -> None:
    """Session-end callback: persist turns to AgentCore Memory for SUMMARY + USER_PREFERENCE extraction."""
    logger.info("persist_session_callback fired — persisting session to memory")
    try:
        await callback_context.add_session_to_memory()
        logger.info("persist_session_callback: memory persist succeeded")
    except Exception:
        logger.warning("persist_session_callback: memory persist failed", exc_info=True)


# ---------------------------------------------------------------------------
# Agent and runtime initialisation
# ---------------------------------------------------------------------------

# Token cache and memory initialised without network calls at import time.
# CognitoTokenCache defers Secrets Manager fetch to first get_token() call.
# Gateway toolset is loaded lazily on first request to stay within 30s cold-start limit.
_token_cache = CognitoTokenCache()
_memory_service = AgentCoreMemoryService(memory_id=MEMORY_ID, region_name=AWS_REGION)

_gateway_toolset_loaded = False
_gateway_toolset: list = []

_model = "bedrock/us.anthropic.claude-sonnet-4-6"

_root_agent: Agent | None = None
_session_service = InMemorySessionService()


def _ensure_gateway_toolset() -> None:
    global _gateway_toolset_loaded, _gateway_toolset
    if not _gateway_toolset_loaded:
        _gateway_toolset = _load_gateway_toolset()
        _gateway_toolset_loaded = True
        logger.info("Gateway toolset loaded: %d toolset(s)", len(_gateway_toolset))
    else:
        logger.debug("Gateway toolset already loaded (cached)")


def _get_root_agent() -> Agent:
    global _root_agent
    if _root_agent is None:
        _ensure_gateway_toolset()
        tools = [preload_memory, save_user_preference] + _gateway_toolset
        logger.info(
            "Creating root agent with %d top-level tool(s): %s",
            len(tools),
            [getattr(t, "name", type(t).__name__) for t in tools],
        )
        agent = Agent(
            name="LapwiseF1Agent",
            model=_model,
            instruction=SYSTEM_PROMPT,
            tools=tools,
        )
        agent.after_agent_callback = persist_session_callback
        _root_agent = agent
    return _root_agent


async def handle_session(
    user_message: str,
    session_id: str | None = None,
    user_id: str = "anonymous",
) -> tuple[str, str]:
    """Run one user turn and return (response_text, session_id)."""

    sid = session_id or str(uuid.uuid4())

    try:
        from aws_xray_sdk.core import xray_recorder  # type: ignore[import]

        segment = xray_recorder.begin_segment("LapwiseF1Agent")
        segment.put_annotation("session_id", sid)
        segment.put_annotation("user_id", user_id)
        _use_xray = True
    except Exception:
        _use_xray = False

    logger.info(
        json.dumps({
            "event": "session_start",
            "session_id": sid,
            "user_id": user_id,
            "message_length": len(user_message),
            "message_preview": user_message[:120],
        })
    )

    try:
        runner = Runner(
            app_name="LapwiseF1Agent",
            agent=_get_root_agent(),
            session_service=_session_service,
            memory_service=_memory_service,
        )
        existing = await _session_service.get_session(
            app_name="LapwiseF1Agent", user_id=user_id, session_id=sid
        )
        if not existing:
            await _session_service.create_session(
                app_name="LapwiseF1Agent", user_id=user_id, session_id=sid
            )
            logger.info("Created new session: %s", sid)
        else:
            logger.info("Resumed existing session: %s", sid)

        from google.genai.types import Content, Part  # type: ignore[import]

        user_content = Content(role="user", parts=[Part(text=user_message)])
        result_text = ""
        event_count = 0

        async for event in runner.run_async(
            user_id=user_id, session_id=sid, new_message=user_content
        ):
            event_count += 1
            author = getattr(event, "author", "?")
            has_text = False
            has_tool_call = False
            has_tool_result = False
            if getattr(event, "content", None):
                for part in event.content.parts or []:
                    if getattr(part, "text", None):
                        result_text += part.text
                        has_text = True
                    if getattr(part, "function_call", None):
                        fc = part.function_call
                        logger.info(
                            "Tool call: author=%s name=%s args_keys=%s",
                            author,
                            getattr(fc, "name", "?"),
                            list((getattr(fc, "args", None) or {}).keys()),
                        )
                        has_tool_call = True
                    if getattr(part, "function_response", None):
                        fr = part.function_response
                        resp_preview = str(getattr(fr, "response", ""))[:200]
                        logger.info(
                            "Tool response: name=%s response_preview=%s",
                            getattr(fr, "name", "?"),
                            resp_preview,
                        )
                        has_tool_result = True
            logger.debug(
                "ADK event #%d: author=%s text=%s tool_call=%s tool_result=%s",
                event_count, author, has_text, has_tool_call, has_tool_result,
            )

        logger.info(
            json.dumps({
                "event": "session_end",
                "session_id": sid,
                "user_id": user_id,
                "adk_events": event_count,
                "response_length": len(result_text),
                "response_preview": result_text[:120],
            })
        )
        return result_text, sid
    finally:
        if _use_xray:
            try:
                xray_recorder.end_segment()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# BedrockAgentCoreApp entrypoint
# ---------------------------------------------------------------------------

try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp  # type: ignore[import]

    app = BedrockAgentCoreApp()

    @app.entrypoint
    async def agent_entrypoint(payload, context=None) -> dict:
        # BedrockAgentCoreApp passes the request payload dict directly.
        body = payload if isinstance(payload, dict) else {}
        logger.info(
            "Entrypoint received: body_type=%s body_keys=%s",
            type(body).__name__,
            list(body.keys()) if isinstance(body, dict) else repr(body)[:120],
        )
        # `agentcore invoke` sends {"prompt": ...}; custom clients may send {"message": ...}
        message = body.get("message") or body.get("prompt") or ""
        session_id = body.get("session_id") if isinstance(body, dict) else None
        user_id = body.get("user_id", "anonymous") if isinstance(body, dict) else "anonymous"
        logger.info(
            "Parsed: message_length=%d session_id=%s user_id=%s",
            len(message), session_id, user_id,
        )
        response, sid = await handle_session(message, session_id=session_id, user_id=user_id)
        return {"response": response, "session_id": sid}

    if __name__ == "__main__":
        app.run()

except ImportError:
    logger.warning("bedrock-agentcore not installed — BedrockAgentCoreApp unavailable (dev mode)")
    app = None  # type: ignore[assignment]
