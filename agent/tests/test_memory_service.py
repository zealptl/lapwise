"""Unit tests for AgentCoreMemoryService."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_search_memory_returns_empty_when_no_memory_id():
    from memory import AgentCoreMemoryService

    svc = AgentCoreMemoryService(memory_id=None)
    result = await svc.search_memory(app_name="test", user_id="user1", query="Monaco picks")
    assert result.memories == []


@pytest.mark.asyncio
async def test_add_session_to_memory_noop_when_no_memory_id():
    from memory import AgentCoreMemoryService

    svc = AgentCoreMemoryService(memory_id=None)
    session = MagicMock()
    # Should not raise
    await svc.add_session_to_memory(session)


@pytest.mark.asyncio
async def test_add_session_to_memory_calls_create_event():
    mock_client = MagicMock()
    mock_client.get_memory_strategies.return_value = []
    mock_client.create_event = MagicMock()

    with patch("memory.AgentCoreMemoryService.__init__") as mock_init:
        from memory import AgentCoreMemoryService

        svc = AgentCoreMemoryService.__new__(AgentCoreMemoryService)
        svc._memory_id = "mem-123"
        svc._client = mock_client
        svc._strategy_namespaces = []

    # Build a mock session with one user event
    mock_part = MagicMock()
    mock_part.text = "Who should I pick for Monaco?"

    mock_event = MagicMock()
    mock_event.author = "user"
    mock_event.content = MagicMock()
    mock_event.content.parts = [mock_part]

    mock_session = MagicMock()
    mock_session.id = "sess-abc"
    mock_session.user_id = "user1"
    mock_session.events = [mock_event]

    await svc.add_session_to_memory(mock_session)

    mock_client.create_event.assert_called_once()
    call_kwargs = mock_client.create_event.call_args.kwargs
    assert call_kwargs["memory_id"] == "mem-123"
    assert call_kwargs["actor_id"] == "user1"
    assert call_kwargs["session_id"] == "sess-abc"
    assert ("Who should I pick for Monaco?", "USER") in call_kwargs["messages"]


@pytest.mark.asyncio
async def test_add_session_to_memory_skips_events_without_text():
    mock_client = MagicMock()
    mock_client.create_event = MagicMock()

    from memory import AgentCoreMemoryService

    svc = AgentCoreMemoryService.__new__(AgentCoreMemoryService)
    svc._memory_id = "mem-456"
    svc._client = mock_client
    svc._strategy_namespaces = []

    # Event with no text parts
    mock_part = MagicMock()
    mock_part.text = None
    mock_event = MagicMock()
    mock_event.author = "user"
    mock_event.content = MagicMock()
    mock_event.content.parts = [mock_part]

    mock_session = MagicMock()
    mock_session.id = "sess-xyz"
    mock_session.user_id = "user2"
    mock_session.events = [mock_event]

    await svc.add_session_to_memory(mock_session)
    mock_client.create_event.assert_not_called()
