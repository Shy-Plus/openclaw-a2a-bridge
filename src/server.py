#!/usr/bin/env python3
"""
A2A Server — Wraps an OpenClaw agent as a Google A2A-compliant server.

This server exposes any OpenClaw agent via the A2A protocol, enabling
discovery and communication from other A2A-compatible agents.

Endpoints:
    GET  /.well-known/agent.json   → Agent Card (discovery)
    POST /                         → JSON-RPC message handling
    POST / (streaming)             → SSE streaming responses

Usage:
    python -m src.server [--port 9100] [--host 0.0.0.0] [--agent-card cards/agent_card.json]
"""

import argparse
import json
import logging
import sys

import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
)

from .config import (
    DEFAULT_AGENT_CARD_PATH,
    GATEWAY_TOKEN,
    LOCAL_API_URL,
    LOCAL_HOST,
    LOCAL_PORT,
    LOCAL_PUBLIC_URL,
)
from .adapter import OpenResponsesAdapter, OpenResponsesAgentExecutor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("a2a-server")


def load_agent_card(card_path: str, public_url: str) -> AgentCard:
    """
    Load agent card from JSON file and build the AgentCard object.

    Args:
        card_path: Path to the agent card JSON file.
        public_url: Externally reachable base URL for the agent.

    Returns:
        AgentCard instance ready for A2A protocol.
    """
    with open(card_path) as f:
        card_data = json.load(f)

    # Override URL with externally reachable public URL
    card_data["url"] = public_url.rstrip("/") + "/"

    skills = [
        AgentSkill(
            id=s["id"],
            name=s["name"],
            description=s["description"],
            tags=s.get("tags", []),
            examples=s.get("examples"),
        )
        for s in card_data.get("skills", [])
    ]

    provider = None
    if "provider" in card_data:
        provider = AgentProvider(
            organization=card_data["provider"]["organization"],
            url=card_data["provider"]["url"],
        )

    return AgentCard(
        name=card_data["name"],
        description=card_data.get("description", ""),
        url=card_data["url"],
        version=card_data.get("version", "1.0.0"),
        provider=provider,
        default_input_modes=card_data.get("default_input_modes", ["text"]),
        default_output_modes=card_data.get("default_output_modes", ["text"]),
        capabilities=AgentCapabilities(
            streaming=card_data.get("capabilities", {}).get("streaming", True)
        ),
        skills=skills,
    )


def main():
    """Entry point for the A2A server."""
    parser = argparse.ArgumentParser(description="A2A Server for OpenClaw Agent")
    parser.add_argument(
        "--host", default=LOCAL_HOST,
        help=f"Bind host (default: {LOCAL_HOST})",
    )
    parser.add_argument(
        "--port", type=int, default=LOCAL_PORT,
        help=f"Bind port (default: {LOCAL_PORT})",
    )
    parser.add_argument(
        "--public-url", default=None,
        help="Externally reachable base URL advertised in Agent Card",
    )
    parser.add_argument(
        "--agent-card", default=DEFAULT_AGENT_CARD_PATH,
        help="Path to agent card JSON",
    )
    parser.add_argument(
        "--api-url", default=LOCAL_API_URL,
        help="OpenResponses API URL",
    )
    parser.add_argument(
        "--token", default=GATEWAY_TOKEN,
        help="Gateway auth token (prefer A2A_GATEWAY_TOKEN env var)",
    )
    parser.add_argument(
        "--model", default="echo",
        help="Model name for OpenResponses (default: echo)",
    )
    args = parser.parse_args()

    if not args.token:
        logger.error(
            "No gateway token found. "
            "Set A2A_GATEWAY_TOKEN env var or configure openclaw.json"
        )
        sys.exit(1)

    # Load agent card
    public_url = args.public_url or LOCAL_PUBLIC_URL
    agent_card = load_agent_card(args.agent_card, public_url)
    logger.info(f"Agent Card: {agent_card.name} v{agent_card.version}")
    logger.info(f"  Skills: {[s.name for s in agent_card.skills]}")
    logger.info(f"  URL: {agent_card.url}")

    # Create the OpenResponses adapter
    adapter = OpenResponsesAdapter(
        api_url=args.api_url,
        token=args.token,
        model=args.model,
    )
    logger.info(f"OpenResponses API: {args.api_url}")

    # Create the A2A request handler
    executor = OpenResponsesAgentExecutor(adapter)
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    # Build the A2A Starlette application
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    logger.info(f"Starting A2A Server on {args.host}:{args.port}")
    logger.info(
        f"Agent Card available at: "
        f"http://{args.host}:{args.port}/.well-known/agent.json"
    )

    uvicorn.run(server.build(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
