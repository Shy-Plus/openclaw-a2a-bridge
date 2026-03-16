#!/usr/bin/env python3
"""
A2A Client — Discover and send tasks to A2A-compliant agents.

Supports three modes:
    - Discovery only: fetch and display the agent's capabilities
    - One-shot: send a single message and print the response
    - Interactive: start a chat session with context persistence

Usage:
    # Discover an agent
    python -m src.client --target http://agent-host:9100 --discover-only

    # Send a message
    python -m src.client --target http://agent-host:9100 --message "Hello!"

    # Interactive chat
    python -m src.client --target http://agent-host:9100

    # Streaming mode
    python -m src.client --target http://agent-host:9100 -m "Tell me a story" --stream
"""

import argparse
import asyncio
import json
import logging
import sys
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("a2a-client")


def _make_client(**kwargs) -> httpx.AsyncClient:
    """Create httpx client that bypasses system proxy for local/tailnet connections."""
    transport = httpx.AsyncHTTPTransport(proxy=None)
    return httpx.AsyncClient(transport=transport, **kwargs)


async def discover_agent(base_url: str) -> AgentCard:
    """
    Fetch the agent card from a remote A2A server.

    Args:
        base_url: The base URL of the A2A server (e.g., http://host:9100).

    Returns:
        The AgentCard describing the remote agent's capabilities.
    """
    async with _make_client() as client:
        resolver = A2ACardResolver(
            httpx_client=client,
            base_url=base_url,
        )
        card = await resolver.get_agent_card()
        return card


def print_agent_card(card: AgentCard):
    """Pretty-print an agent card to stdout."""
    print("\n" + "=" * 60)
    print(f"🤖 Agent: {card.name}")
    print(f"   Version: {card.version}")
    print(f"   URL: {card.url}")
    if card.description:
        print(f"   Description: {card.description}")
    if card.provider:
        print(f"   Provider: {card.provider.organization}")
    if card.capabilities:
        print(f"   Streaming: {card.capabilities.streaming}")
    if card.skills:
        print(f"\n   Skills ({len(card.skills)}):")
        for skill in card.skills:
            print(f"     • {skill.name}: {skill.description}")
            if skill.examples:
                print(f"       Examples: {', '.join(skill.examples[:3])}")
    print("=" * 60 + "\n")


async def send_message(
    base_url: str,
    card: AgentCard,
    text: str,
    stream: bool = False,
    context_id: str | None = None,
) -> str:
    """
    Send a message to an A2A agent and return the response.

    Args:
        base_url: The base URL of the A2A server.
        card: The AgentCard of the target agent.
        text: The message text to send.
        stream: Whether to use SSE streaming mode.
        context_id: Optional context ID for conversation continuity.

    Returns:
        The response text from the agent.
    """
    async with _make_client(timeout=120.0) as httpx_client:
        client = A2AClient(httpx_client=httpx_client, agent_card=card)

        payload = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": text}],
                "messageId": uuid4().hex,
            },
        }

        if context_id:
            payload["message"]["contextId"] = context_id

        if stream:
            request = SendStreamingMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**payload),
            )
            print(f"\n📨 Sending (streaming) to {card.name}: \"{text}\"")
            print(f"📥 Response from {card.name}:")
            print("-" * 40)

            full_text = ""
            async for chunk in client.send_message_streaming(request):
                chunk_data = chunk.model_dump(mode="json", exclude_none=True)
                result = chunk_data.get("result", {})
                if isinstance(result, dict):
                    parts = result.get("parts", [])
                    for part in parts:
                        if part.get("kind") == "text":
                            t = part.get("text", "")
                            print(t, end="", flush=True)
                            full_text += t
                    status = result.get("status", {})
                    if status:
                        state = status.get("state", "")
                        if state and state != "working":
                            msg = status.get("message", {})
                            if isinstance(msg, dict):
                                for p in msg.get("parts", []):
                                    if p.get("kind") == "text":
                                        t = p.get("text", "")
                                        print(t, end="", flush=True)
                                        full_text += t

            print("\n" + "-" * 40)
            return full_text
        else:
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**payload),
            )
            print(f"\n📨 Sending to {card.name}: \"{text}\"")

            response = await client.send_message(request)
            resp_data = response.model_dump(mode="json", exclude_none=True)

            # Extract text from response
            result = resp_data.get("result", {})
            texts = []
            if isinstance(result, dict):
                parts = result.get("parts", [])
                for part in parts:
                    if part.get("kind") == "text":
                        texts.append(part["text"])
                status = result.get("status", {})
                if status:
                    msg = status.get("message", {})
                    if isinstance(msg, dict):
                        for p in msg.get("parts", []):
                            if p.get("kind") == "text":
                                texts.append(p["text"])
                for artifact in result.get("artifacts", []):
                    for p in artifact.get("parts", []):
                        if p.get("kind") == "text":
                            texts.append(p["text"])

            response_text = "\n".join(texts) if texts else json.dumps(resp_data, indent=2)
            print(f"📥 Response from {card.name}:")
            print("-" * 40)
            print(response_text)
            print("-" * 40)
            return response_text


async def interactive_mode(
    base_url: str, card: AgentCard, stream: bool = False
):
    """
    Interactive chat mode with persistent context.

    Args:
        base_url: The base URL of the A2A server.
        card: The AgentCard of the target agent.
        stream: Whether to use SSE streaming mode.
    """
    context_id = uuid4().hex
    print(f"\n💬 Interactive chat with {card.name}")
    print(f"   (context: {context_id[:8]}...)")
    print("   Type 'quit' or 'exit' to leave.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye!")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            print("👋 Bye!")
            break

        if not user_input:
            continue

        try:
            await send_message(
                base_url, card, user_input,
                stream=stream, context_id=context_id,
            )
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Entry point for the A2A client."""
    parser = argparse.ArgumentParser(
        description="A2A Client for Agent Communication"
    )
    parser.add_argument(
        "--target", required=True,
        help="Target agent URL (e.g. http://agent-host:9100)",
    )
    parser.add_argument(
        "--message", "-m",
        help="Message to send (omit for interactive mode)",
    )
    parser.add_argument(
        "--stream", "-s", action="store_true",
        help="Use streaming mode",
    )
    parser.add_argument(
        "--discover-only", "-d", action="store_true",
        help="Only discover and print agent card",
    )
    args = parser.parse_args()

    base_url = args.target.rstrip("/")

    # Step 1: Discover the agent
    print(f"🔍 Discovering agent at {base_url}...")
    try:
        card = await discover_agent(base_url)
        print_agent_card(card)
    except Exception as e:
        print(f"❌ Failed to discover agent: {e}")
        sys.exit(1)

    if args.discover_only:
        return

    # Step 2: Send message or enter interactive mode
    if args.message:
        await send_message(base_url, card, args.message, stream=args.stream)
    else:
        await interactive_mode(base_url, card, stream=args.stream)


if __name__ == "__main__":
    asyncio.run(main())
