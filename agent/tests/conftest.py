"""Pytest fixtures shared across agent unit tests.

The agent runs in its container with the app directory on ``sys.path`` (``main.py``
does ``from cognito import ...``). Mirror that here so tests import the modules as
top-level names, exactly as the runtime does.
"""

import pathlib
import sys

# agent/tests/conftest.py -> agent/ -> agent/LapwiseF1Agent/app/LapwiseF1Agent
APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "LapwiseF1Agent" / "app" / "LapwiseF1Agent"
sys.path.insert(0, str(APP_DIR))
