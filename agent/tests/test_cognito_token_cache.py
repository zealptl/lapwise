"""Unit tests for CognitoTokenCache."""

import json
import os
import time
from unittest.mock import MagicMock, patch

import pytest


def _make_cache(env: dict | None = None):
    """Import and instantiate CognitoTokenCache with the given env vars."""
    clean_env = env or {}
    with patch.dict(os.environ, clean_env, clear=True):
        import importlib
        import cognito as mod

        importlib.reload(mod)
        return mod.CognitoTokenCache()


def test_returns_none_when_secret_arn_absent():
    cache = _make_cache({})
    assert cache.get_token() is None


def test_returns_none_when_secret_arn_empty():
    cache = _make_cache({"COGNITO_CLIENT_A_SECRET_ARN": ""})
    assert cache.get_token() is None


def test_fetches_secret_once_at_cold_start():
    secret_payload = json.dumps(
        {"client_secret": "secret123", "token_url": "https://example.auth.us-east-1.amazoncognito.com/oauth2/token"}
    )
    mock_sm = MagicMock()
    mock_sm.get_secret_value.return_value = {"SecretString": secret_payload}

    env = {
        "COGNITO_CLIENT_A_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123:secret/test",
        "COGNITO_CLIENT_A_ID": "client_id_abc",
    }
    with patch.dict(os.environ, env, clear=True):
        with patch("boto3.client", return_value=mock_sm):
            import importlib
            import cognito as mod

            importlib.reload(mod)
            cache = mod.CognitoTokenCache()
            # Secret load is deferred to the first get_token() call (lazy cold start).
            # Patch _refresh_token so we exercise the load path without a real HTTP call.
            with patch.object(cache, "_refresh_token"):
                cache.get_token()
                cache.get_token()

    mock_sm.get_secret_value.assert_called_once_with(
        SecretId="arn:aws:secretsmanager:us-east-1:123:secret/test"
    )
    assert cache._client_secret == "secret123"


def test_token_is_cached_on_second_call():
    """Verify that _refresh_token is not called again while the token is still valid."""
    secret_payload = json.dumps(
        {"client_secret": "s", "token_url": "https://example.com/oauth2/token"}
    )
    mock_sm = MagicMock()
    mock_sm.get_secret_value.return_value = {"SecretString": secret_payload}

    env = {
        "COGNITO_CLIENT_A_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123:secret/test",
        "COGNITO_CLIENT_A_ID": "cid",
    }
    with patch.dict(os.environ, env, clear=True):
        with patch("boto3.client", return_value=mock_sm):
            import importlib
            import cognito as mod

            importlib.reload(mod)
            cache = mod.CognitoTokenCache()

    # Pre-seed a valid token so _refresh_token is never called
    cache._token = "tok_abc"
    cache._expires_at = time.time() + 3600

    with patch.object(cache, "_refresh_token") as mock_refresh:
        result1 = cache.get_token()
        result2 = cache.get_token()

    assert result1 == "tok_abc"
    assert result2 == "tok_abc"
    mock_refresh.assert_not_called()
