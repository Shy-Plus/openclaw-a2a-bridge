"""
Configuration for A2A Bridge.

All settings are loaded from environment variables or .env file.
Centralizes endpoint URLs, tokens, and network settings.

Required environment variables:
    A2A_GATEWAY_TOKEN   - Gateway authentication token

Optional environment variables:
    A2A_LOCAL_HOST      - Local agent Tailscale IP (default: 0.0.0.0)
    A2A_LOCAL_PORT      - Local A2A server port (default: 9100)
    A2A_LOCAL_API       - Local OpenResponses API URL
    A2A_REMOTE_HOST     - Remote agent Tailscale IP
    A2A_REMOTE_PORT     - Remote A2A server port (default: 9100)
    A2A_REMOTE_API      - Remote OpenResponses API URL
    A2A_PUBLIC_URL      - Externally reachable URL for Agent Card
    A2A_REMOTE_PUBLIC_URL - Remote agent's public URL
    A2A_AGENT_CARD      - Path to agent card JSON file
    A2A_TRAFFIC_LOG     - Path to traffic log file
"""

import json
import os
from pathlib import Path

# ─── Network Configuration ────────────────────────────────────────────

# Local agent (the machine running this server)
LOCAL_HOST = os.getenv("A2A_LOCAL_HOST", "0.0.0.0")
LOCAL_PORT = int(os.getenv("A2A_LOCAL_PORT", "9100"))
LOCAL_API_URL = os.getenv(
    "A2A_LOCAL_API", "http://localhost:18789/v1/responses"
)

# Remote agent (the peer machine)
REMOTE_HOST = os.getenv("A2A_REMOTE_HOST", "")
REMOTE_PORT = int(os.getenv("A2A_REMOTE_PORT", "9100"))
REMOTE_API_URL = os.getenv(
    "A2A_REMOTE_API",
    f"http://{REMOTE_HOST}:{REMOTE_PORT}/v1/responses" if REMOTE_HOST else "",
)

# ─── Public URL (for Agent Card advertisement) ────────────────────────
# Override with A2A_PUBLIC_URL for custom setups (ngrok, domain, etc.)
LOCAL_PUBLIC_URL = os.getenv(
    "A2A_PUBLIC_URL", f"http://{LOCAL_HOST}:{LOCAL_PORT}"
)
REMOTE_PUBLIC_URL = os.getenv(
    "A2A_REMOTE_PUBLIC_URL",
    f"http://{REMOTE_HOST}:{REMOTE_PORT}" if REMOTE_HOST else "",
)


def _load_gateway_token() -> str:
    """
    Load the gateway auth token.

    Priority:
    1. A2A_GATEWAY_TOKEN environment variable
    2. OpenClaw config file (~/.openclaw/openclaw.json)
    """
    env_token = os.getenv("A2A_GATEWAY_TOKEN", "")
    if env_token:
        return env_token

    config_path = Path.home() / ".openclaw" / "openclaw.json"
    try:
        with open(config_path) as f:
            config = json.load(f)
        return config.get("gateway", {}).get("auth", {}).get("token", "")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return ""


GATEWAY_TOKEN = _load_gateway_token()

# ─── Agent Card Paths ─────────────────────────────────────────────────
AGENT_CARD_DIR = Path(__file__).parent.parent / "cards"
DEFAULT_AGENT_CARD_PATH = os.getenv(
    "A2A_AGENT_CARD",
    str(AGENT_CARD_DIR / "agent_card.json"),
)

# ─── Logging ──────────────────────────────────────────────────────────
TRAFFIC_LOG_PATH = os.getenv(
    "A2A_TRAFFIC_LOG",
    str(Path.home() / ".openclaw" / "logs" / "a2a-traffic.log"),
)
