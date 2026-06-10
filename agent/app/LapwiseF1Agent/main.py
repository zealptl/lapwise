"""LapwiseF1Agent — GoogleADK agent for F1 Fantasy recommendations on BedrockAgentCore."""

import json
import logging
import os
import uuid

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.tools import preload_memory

from .cognito import CognitoTokenCache
from .memory import AgentCoreMemoryService

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


def _load_gateway_tools(token_cache: CognitoTokenCache) -> list:
    """Load tool definitions from AgentCore Gateway. Returns [] when gateway URL is not set."""
    if not GATEWAY_URL:
        logger.warning(
            "AGENTCORE_GATEWAY_LAPWISEGATEWAY_URL not set — skipping gateway tools (dev mode)"
        )
        return []
    try:
        from bedrock_agentcore.gateway import GatewayClient  # type: ignore[import]

        token = token_cache.get_token()
        client = GatewayClient(gateway_url=GATEWAY_URL, token=token)
        tools = client.list_tools()
        logger.info("Loaded %d tools from AgentCore Gateway", len(tools))
        return tools
    except Exception:
        logger.warning("Failed to load gateway tools", exc_info=True)
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
    await callback_context.add_session_to_memory()


# ---------------------------------------------------------------------------
# Agent and runtime initialisation
# ---------------------------------------------------------------------------

_token_cache = CognitoTokenCache()
_gateway_tools = _load_gateway_tools(_token_cache)

root_agent = Agent(
    name="LapwiseF1Agent",
    model="anthropic.claude-sonnet-4-6",
    instruction=SYSTEM_PROMPT,
    tools=[preload_memory, save_user_preference, *_gateway_tools],
)
root_agent.after_agent_callback = persist_session_callback

_memory_service = AgentCoreMemoryService(memory_id=MEMORY_ID, region_name=AWS_REGION)


async def handle_session(
    user_message: str,
    session_id: str | None = None,
    user_id: str = "anonymous",
) -> str:
    """Run one user turn and return the agent's final response text."""
    sid = session_id or str(uuid.uuid4())

    try:
        from aws_xray_sdk.core import xray_recorder  # type: ignore[import]

        segment = xray_recorder.begin_segment("LapwiseF1Agent")
        segment.put_annotation("session_id", sid)
        segment.put_annotation("user_id", user_id)
        _use_xray = True
    except Exception:
        _use_xray = False

    logger.info(json.dumps({"event": "session_start", "session_id": sid, "user_id": user_id}))

    try:
        runner = Runner(
            app_name="LapwiseF1Agent",
            agent=root_agent,
            memory_service=_memory_service,
        )
        session = await runner.session_service.get_or_create_session(
            app_name="LapwiseF1Agent", user_id=user_id, session_id=sid
        )

        from google.adk.types import Content, Part  # type: ignore[import]

        user_content = Content(role="user", parts=[Part(text=user_message)])
        result_text = ""

        async for event in runner.run_async(
            user_id=user_id, session_id=sid, new_message=user_content
        ):
            if getattr(event, "content", None):
                for part in event.content.parts or []:
                    if getattr(part, "text", None):
                        result_text += part.text

        logger.info(
            json.dumps(
                {
                    "event": "session_end",
                    "session_id": sid,
                    "user_id": user_id,
                    "response_length": len(result_text),
                }
            )
        )
        return result_text
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

    app = BedrockAgentCoreApp(name="LapwiseF1Agent")

    @app.entrypoint
    async def agent_entrypoint(request) -> dict:
        body = getattr(request, "body", {}) or {}
        message = body.get("message", "")
        session_id = body.get("session_id")
        user_id = body.get("user_id", "anonymous")
        response = await handle_session(message, session_id=session_id, user_id=user_id)
        return {"response": response, "session_id": session_id}

    if __name__ == "__main__":
        app.run()

except ImportError:
    logger.warning("bedrock-agentcore not installed — BedrockAgentCoreApp unavailable (dev mode)")
    app = None  # type: ignore[assignment]
