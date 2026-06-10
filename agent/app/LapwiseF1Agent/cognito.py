"""Cognito M2M token cache — fetches client credentials tokens via Secrets Manager."""

import base64
import json
import logging
import os
import time
import urllib.request

import boto3

logger = logging.getLogger(__name__)


class CognitoTokenCache:
    """Fetches an M2M access token using client credentials stored in Secrets Manager.

    The raw secret is fetched once at cold start via the Secrets Manager ARN stored in
    COGNITO_CLIENT_A_SECRET_ARN. The token itself is cached in memory until expiry.
    Returns None in dev mode (when COGNITO_CLIENT_A_SECRET_ARN is absent).
    """

    def __init__(self) -> None:
        self._secret_arn: str | None = os.getenv("COGNITO_CLIENT_A_SECRET_ARN")
        self._client_id: str | None = os.getenv("COGNITO_CLIENT_A_ID")
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._client_secret: str | None = None
        self._token_url: str | None = None

        if self._secret_arn:
            self._load_secret()

    def _load_secret(self) -> None:
        """Fetch secret from Secrets Manager at cold start."""
        try:
            sm = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "us-east-1"))
            response = sm.get_secret_value(SecretId=self._secret_arn)
            secret = json.loads(response["SecretString"])
            self._client_secret = secret.get("client_secret")
            self._token_url = secret.get("token_url")
        except Exception:
            logger.exception("Failed to load Cognito client secret from Secrets Manager")

    def get_token(self) -> str | None:
        """Return a valid access token, refreshing if needed. Returns None in dev mode."""
        if not self._secret_arn:
            return None
        if self._token and time.time() < self._expires_at - 30:
            return self._token
        self._refresh_token()
        return self._token

    def _refresh_token(self) -> None:
        if not self._token_url or not self._client_id or not self._client_secret:
            logger.warning("Cannot refresh Cognito token — missing token_url or client credentials")
            return
        try:
            credentials = base64.b64encode(
                f"{self._client_id}:{self._client_secret}".encode()
            ).decode()
            req = urllib.request.Request(
                self._token_url,
                data=b"grant_type=client_credentials",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            with urllib.request.urlopen(req) as resp:
                body = json.loads(resp.read())
            self._token = body["access_token"]
            self._expires_at = time.time() + body.get("expires_in", 3600)
        except Exception:
            logger.exception("Failed to refresh Cognito M2M token")
