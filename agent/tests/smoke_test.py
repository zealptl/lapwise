#!/usr/bin/env python3
"""Smoke test: sends a test message to the local agentcore dev server (port 8080).

Usage:
    # Start local server first:
    #   cd agent && agentcore dev --port 8080
    python -m agent.tests.smoke_test
"""

import json
import sys
import urllib.request

PORT = 8080
URL = f"http://localhost:{PORT}"


def run_smoke_test() -> bool:
    payload = json.dumps({"message": "What drivers should I pick for Monaco?"}).encode()
    req = urllib.request.Request(
        URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read())
        assert body.get("response"), f"Empty response body: {body}"
        print(f"✓ Smoke test passed. Response length: {len(body['response'])} chars")
        return True
    except AssertionError as exc:
        print(f"✗ Smoke test failed: {exc}")
        return False
    except Exception as exc:
        print(f"✗ Smoke test error (is the server running on port {PORT}?): {exc}")
        return False


if __name__ == "__main__":
    sys.exit(0 if run_smoke_test() else 1)
