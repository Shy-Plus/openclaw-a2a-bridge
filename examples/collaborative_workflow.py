#!/usr/bin/env python3
"""
Collaborative Workflow Example — Chain multiple A2A agents for complex tasks.

This example demonstrates how to build a multi-step workflow where
different agents handle different parts of a task pipeline.

The pattern:
    Agent A (Research)  →  Agent B (Create)  →  Agent A (Review)

Usage:
    python examples/collaborative_workflow.py \
        --researcher http://agent-a:9100 \
        --creator http://agent-b:9100 \
        --topic "AI agents in 2025"
"""

import argparse
import asyncio
import json
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest


def _make_client(**kwargs) -> httpx.AsyncClient:
    """Create httpx client bypassing system proxy."""
    transport = httpx.AsyncHTTPTransport(proxy=None)
    return httpx.AsyncClient(transport=transport, **kwargs)


async def send_to_agent(
    client: httpx.AsyncClient, url: str, message: str
) -> str:
    """
    Discover an agent and send it a message.

    Args:
        client: The httpx async client.
        url: The A2A server URL.
        message: The message to send.

    Returns:
        The agent's response text.
    """
    resolver = A2ACardResolver(httpx_client=client, base_url=url)
    card = await resolver.get_agent_card()

    a2a = A2AClient(httpx_client=client, agent_card=card)
    request = SendMessageRequest(
        id=str(uuid4()),
        params=MessageSendParams(
            message={
                "role": "user",
                "parts": [{"kind": "text", "text": message}],
                "messageId": uuid4().hex,
            }
        ),
    )

    response = await a2a.send_message(request)
    data = response.model_dump(mode="json", exclude_none=True)

    result = data.get("result", {})
    texts = []
    if isinstance(result, dict):
        for part in result.get("parts", []):
            if part.get("kind") == "text":
                texts.append(part["text"])
        status = result.get("status", {})
        if isinstance(status, dict):
            msg = status.get("message", {})
            if isinstance(msg, dict):
                for p in msg.get("parts", []):
                    if p.get("kind") == "text":
                        texts.append(p["text"])

    return "\n".join(texts) if texts else str(data)


async def run_workflow(
    researcher_url: str, creator_url: str, topic: str
):
    """
    Execute a 3-step collaborative workflow.

    Steps:
        1. Researcher agent gathers key points about the topic
        2. Creator agent writes content based on the research
        3. Researcher agent reviews and provides feedback
    """
    async with _make_client(timeout=120.0) as client:
        print(f"\n{'=' * 60}")
        print(f"🔬 Collaborative Workflow: {topic}")
        print(f"{'=' * 60}")

        # Step 1: Research
        print("\n📋 Step 1/3: Research Phase")
        research_prompt = (
            f"Research the topic '{topic}' and provide 5 key points "
            f"with brief explanations. Be concise and factual."
        )
        research = await send_to_agent(
            client, researcher_url, research_prompt
        )
        print(f"   ✅ Research gathered ({len(research)} chars)")

        # Step 2: Content Creation
        print("\n📋 Step 2/3: Content Creation")
        create_prompt = (
            f"Based on the following research, write a compelling "
            f"blog post introduction (2-3 paragraphs) about '{topic}':\n\n"
            f"{research}"
        )
        content = await send_to_agent(client, creator_url, create_prompt)
        print(f"   ✅ Content created ({len(content)} chars)")

        # Step 3: Review
        print("\n📋 Step 3/3: Review Phase")
        review_prompt = (
            f"Review this blog post introduction for accuracy and "
            f"suggest one improvement:\n\n{content}"
        )
        review = await send_to_agent(client, researcher_url, review_prompt)
        print(f"   ✅ Review complete ({len(review)} chars)")

        # Print results
        print(f"\n{'=' * 60}")
        print("📝 FINAL OUTPUT")
        print(f"{'=' * 60}")
        print(f"\n--- Content ---\n{content}")
        print(f"\n--- Review ---\n{review}")
        print(f"\n{'=' * 60}")
        print("🎉 Workflow complete!")


async def main():
    parser = argparse.ArgumentParser(
        description="Collaborative Workflow — Multi-Agent Pipeline"
    )
    parser.add_argument(
        "--researcher", required=True,
        help="Researcher agent URL",
    )
    parser.add_argument(
        "--creator", required=True,
        help="Creator agent URL",
    )
    parser.add_argument(
        "--topic", default="The future of AI agents",
        help="Topic for the workflow (default: The future of AI agents)",
    )
    args = parser.parse_args()

    await run_workflow(args.researcher, args.creator, args.topic)


if __name__ == "__main__":
    asyncio.run(main())
