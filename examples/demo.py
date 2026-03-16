#!/usr/bin/env python3
"""
A2A Bridge Demo — Demonstrates multi-agent collaboration via A2A protocol.

This script showcases:
1. Discovering agents via A2A protocol
2. Sending tasks between agents
3. Cross-agent collaborative workflows

Prerequisites:
    Start A2A servers on both machines first:
        Machine A:  python -m src.server --agent-card cards/agent_card.json
        Machine B:  python -m src.server --agent-card cards/remote_agent_card.json

Usage:
    python examples/demo.py --local http://machine-a:9100 --remote http://machine-b:9100
    python examples/demo.py --local http://machine-a:9100  # Single agent mode
"""

import argparse
import asyncio
import json
import sys
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest


def _make_client(**kwargs) -> httpx.AsyncClient:
    """Create httpx client bypassing system proxy."""
    transport = httpx.AsyncHTTPTransport(proxy=None)
    return httpx.AsyncClient(transport=transport, **kwargs)


async def discover_and_print(
    client: httpx.AsyncClient, url: str, label: str
):
    """Discover an agent and display its capabilities."""
    print(f"\n{'=' * 60}")
    print(f"🔍 Discovering {label} at {url}...")
    resolver = A2ACardResolver(httpx_client=client, base_url=url)
    card = await resolver.get_agent_card()
    print(f"✅ Found: {card.name} v{card.version}")
    print(f"   {card.description}")
    print(f"   Skills: {[s.name for s in card.skills]}")
    print(f"{'=' * 60}")
    return card


async def send_task(
    client: httpx.AsyncClient, card, text: str
) -> str:
    """Send a task to an agent and return the response text."""
    a2a_client = A2AClient(httpx_client=client, agent_card=card)
    payload = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": text}],
            "messageId": uuid4().hex,
        },
    }
    request = SendMessageRequest(
        id=str(uuid4()),
        params=MessageSendParams(**payload),
    )
    response = await a2a_client.send_message(request)
    resp_data = response.model_dump(mode="json", exclude_none=True)

    result = resp_data.get("result", {})
    texts = []
    if isinstance(result, dict):
        for part in result.get("parts", []):
            if part.get("kind") == "text":
                texts.append(part["text"])
        status = result.get("status", {})
        if status:
            msg = status.get("message", {})
            if isinstance(msg, dict):
                for p in msg.get("parts", []):
                    if p.get("kind") == "text":
                        texts.append(p["text"])

    return "\n".join(texts) if texts else json.dumps(resp_data, indent=2)


async def demo_discovery(local_url: str, remote_url: str | None):
    """Demo 1: Agent Discovery via A2A Protocol."""
    print("\n" + "🌟" * 30)
    print("  Demo 1: Agent Discovery")
    print("🌟" * 30)

    async with _make_client() as client:
        try:
            local_card = await discover_and_print(
                client, local_url, "Local Agent"
            )
        except Exception as e:
            print(f"⚠️  Could not reach local agent: {e}")
            local_card = None

        remote_card = None
        if remote_url:
            try:
                remote_card = await discover_and_print(
                    client, remote_url, "Remote Agent"
                )
            except Exception as e:
                print(f"⚠️  Could not reach remote agent: {e}")

    return local_card, remote_card


async def demo_single_agent(local_url: str):
    """Demo 2: Single-Agent Task Execution."""
    print("\n" + "🌟" * 30)
    print("  Demo 2: Single-Agent Task")
    print("🌟" * 30)

    async with _make_client(timeout=60.0) as client:
        try:
            resolver = A2ACardResolver(
                httpx_client=client, base_url=local_url
            )
            card = await resolver.get_agent_card()
            print(f"✅ Connected to: {card.name}")
        except Exception as e:
            print(f"❌ Cannot reach agent: {e}")
            return

        task = "What is the A2A (Agent-to-Agent) protocol?"
        print(f"\n📨 Sending: \"{task}\"")
        print("⏳ Waiting for response...")

        response = await send_task(client, card, task)
        print(f"\n📥 Response from {card.name}:")
        print("-" * 40)
        print(response[:500])
        if len(response) > 500:
            print(f"... ({len(response)} chars total)")
        print("-" * 40)


async def demo_collaboration(local_url: str, remote_url: str):
    """Demo 3: Cross-Agent Collaborative Workflow."""
    print("\n" + "🌟" * 30)
    print("  Demo 3: Cross-Agent Collaboration")
    print("  Local researches → Remote creates")
    print("🌟" * 30)

    async with _make_client(timeout=60.0) as client:
        try:
            local_resolver = A2ACardResolver(
                httpx_client=client, base_url=local_url
            )
            local_card = await local_resolver.get_agent_card()
        except Exception:
            print("❌ Local agent not available")
            return

        try:
            remote_resolver = A2ACardResolver(
                httpx_client=client, base_url=remote_url
            )
            remote_card = await remote_resolver.get_agent_card()
        except Exception:
            print("❌ Remote agent not available")
            return

        # Step 1: Local agent researches
        research_task = "Briefly explain Google's A2A protocol in 3 bullet points"
        print(f"\n📋 Step 1: Asking {local_card.name} to research...")
        local_response = await send_task(client, local_card, research_task)
        print(f"   ✅ Research complete: {local_response[:200]}...")

        # Step 2: Remote agent creates content from research
        creative_task = (
            f"Based on this research, write a catchy tweet about "
            f"A2A protocol:\n\n{local_response}"
        )
        print(f"\n📋 Step 2: Asking {remote_card.name} to create...")
        remote_response = await send_task(
            client, remote_card, creative_task
        )
        print(f"   ✅ Creation: {remote_response[:300]}")

        print("\n🎉 Collaborative workflow complete!")


async def main():
    parser = argparse.ArgumentParser(
        description="A2A Bridge Demo — Multi-Agent Collaboration"
    )
    parser.add_argument(
        "--local", required=True,
        help="Local agent URL (e.g., http://192.168.1.10:9100)",
    )
    parser.add_argument(
        "--remote", default=None,
        help="Remote agent URL for collaboration demo",
    )
    args = parser.parse_args()

    print("╔════════════════════════════════════════════════════════════╗")
    print("║       A2A Bridge Demo — Agent Collaboration              ║")
    print("║       Google Agent-to-Agent Protocol (A2A)               ║")
    print("╚════════════════════════════════════════════════════════════╝")

    await demo_discovery(args.local, args.remote)
    await demo_single_agent(args.local)

    if args.remote:
        await demo_collaboration(args.local, args.remote)

    print("\n✨ All demos complete!")


if __name__ == "__main__":
    asyncio.run(main())
