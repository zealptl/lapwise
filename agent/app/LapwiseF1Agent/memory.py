"""AgentCoreMemoryService — GoogleADK BaseMemoryService backed by AWS BedrockAgentCore Memory."""

import logging

from google.adk.memory.base_memory_service import BaseMemoryService, SearchMemoryResponse
from google.adk.memory.memory_entry import MemoryEntry

logger = logging.getLogger(__name__)


class AgentCoreMemoryService(BaseMemoryService):
    """Bridges GoogleADK memory interface to AWS AgentCore Memory resource.

    No-ops silently when memory_id is None so the agent works in dev mode
    without AWS credentials.
    """

    def __init__(self, memory_id: str | None, region_name: str = "us-east-1") -> None:
        self._memory_id = memory_id
        self._region = region_name
        self._client = None
        self._strategy_namespaces: list[str] = []

        if memory_id:
            try:
                from bedrock_agentcore.memory import MemoryClient  # type: ignore[import]

                self._client = MemoryClient(region_name=region_name)
                self._load_strategies()
            except Exception:
                logger.warning("Failed to initialise AgentCore MemoryClient", exc_info=True)

    def _load_strategies(self) -> None:
        try:
            strategies = self._client.get_memory_strategies(memory_id=self._memory_id)
            for s in strategies or []:
                self._strategy_namespaces.extend(s.get("namespaces", []))
        except Exception:
            logger.warning("Failed to load memory strategies", exc_info=True)

    async def search_memory(
        self, *, app_name: str, user_id: str, query: str
    ) -> SearchMemoryResponse:
        if not self._memory_id or not self._client:
            return SearchMemoryResponse(memories=[])

        memories: list[MemoryEntry] = []

        # Short-term: last K turns verbatim
        try:
            with _xray_subsegment("memory.retrieve"):
                turns = self._client.get_last_k_turns(
                    memory_id=self._memory_id,
                    actor_id=user_id,
                    session_id=app_name,
                    k=5,
                )
            for turn in turns or []:
                memories.append(MemoryEntry(content=str(turn), author="system"))
        except Exception:
            logger.warning("Short-term memory search failed", exc_info=True)

        # Long-term: semantic retrieval per strategy namespace
        for ns_template in self._strategy_namespaces:
            try:
                ns = ns_template.replace("{actorId}", user_id)
                with _xray_subsegment("memory.retrieve"):
                    results = self._client.retrieve_memories(
                        memory_id=self._memory_id,
                        namespace=ns,
                        query=query,
                        top_k=5,
                    )
                for r in results or []:
                    memories.append(MemoryEntry(content=str(r), author="system"))
            except Exception:
                logger.warning("Long-term memory search failed for %s", ns_template, exc_info=True)

        return SearchMemoryResponse(memories=memories)

    async def add_session_to_memory(self, session) -> None:  # type: ignore[override]
        if not self._memory_id or not self._client:
            return
        try:
            messages: list[tuple[str, str]] = []
            for event in session.events or []:
                if not getattr(event, "content", None):
                    continue
                role = "USER" if getattr(event, "author", "") == "user" else "ASSISTANT"
                for part in event.content.parts or []:
                    if getattr(part, "text", None):
                        messages.append((part.text, role))

            if messages:
                with _xray_subsegment("memory.store"):
                    self._client.create_event(
                        memory_id=self._memory_id,
                        actor_id=getattr(session, "user_id", "unknown"),
                        session_id=session.id,
                        messages=messages,
                    )
        except Exception:
            logger.warning("Failed to persist session to AgentCore Memory", exc_info=True)


class _xray_subsegment:
    """Lightweight context manager for X-Ray subsegments; no-ops if SDK unavailable."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._recorder = None

    def __enter__(self):
        try:
            from aws_xray_sdk.core import xray_recorder  # type: ignore[import]

            xray_recorder.begin_subsegment(self._name)
            self._recorder = xray_recorder
        except Exception:
            pass
        return self

    def __exit__(self, *_):
        if self._recorder:
            try:
                self._recorder.end_subsegment()
            except Exception:
                pass
