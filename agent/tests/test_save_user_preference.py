"""Unit tests for save_user_preference function tool."""

import importlib
import os
from unittest.mock import patch


def _load_main(memory_id: str | None = None):
    env = {}
    if memory_id:
        env["MEMORY_ID"] = memory_id
    with patch.dict(os.environ, env, clear=True):
        import agent.app.LapwiseF1Agent.main as mod
        importlib.reload(mod)
        return mod


def test_noop_returns_dev_mode_message_when_no_memory_id():
    mod = _load_main(memory_id=None)
    result = mod.save_user_preference("I prefer budget picks under £8M")
    assert "dev mode" in result.lower()


def test_returns_confirmation_when_memory_id_set():
    mod = _load_main(memory_id="mem-123")
    result = mod.save_user_preference("I always want to include Norris")
    assert "I always want to include Norris" in result
    assert "dev mode" not in result.lower()
