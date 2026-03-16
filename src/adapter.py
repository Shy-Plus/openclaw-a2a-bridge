"""
OpenResponses Adapter — bridges A2A protocol to OpenClaw's OpenResponses API.

This is the core adapter that:
1. Receives A2A messages via the AgentExecutor interface
2. Translates them into OpenResponses API calls
3. Streams or returns the response back through the A2A event queue

The adapter handles both synchronous and streaming communication modes,
with built-in traffic logging for debugging and monitoring.
"""

import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from typing import AsyncIterator

import httpx

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Message,
    Part,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from a2a.utils import new_agent_text_message

from .config import TRAFFIC_LOG_PATH

logger = logging.getLogger(__name__)

# ─── Persistent Traffic Logger ─────────────────────────────────────────
os.makedirs(os.path.dirname(TRAFFIC_LOG_PATH), exist_ok=True)

traffic_logger = logging.getLogger("a2a.traffic")
traffic_logger.setLevel(logging.INFO)
traffic_logger.propagate = False  # don't bubble to root logger

_traffic_handler = RotatingFileHandler(
    TRAFFIC_LOG_PATH,
    maxBytes=10 * 1024 * 1024,  # 10 MB per file
    backupCount=5,               # keep 5 rotated files
    encoding="utf-8",
)
_traffic_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)
traffic_logger.addHandler(_traffic_handler)


def _summarize(text: str, max_len: int = 200) -> str:
    """Truncate text for log summaries."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


class OpenResponsesAdapter:
    """
    Calls the OpenResponses API and yields text chunks.

    Supports both streaming (SSE) and non-streaming modes.
    All requests are logged to the traffic log for debugging.

    Args:
        api_url: The OpenResponses API endpoint URL.
        token: Bearer token for authentication.
        model: Model name to use for responses (default: "echo").
    """

    def __init__(self, api_url: str, token: str, model: str = "echo"):
        self.api_url = api_url
        self.token = token
        self.model = model
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an async HTTP client (with proxy bypass)."""
        if self._client is None or self._client.is_closed:
            transport = httpx.AsyncHTTPTransport(proxy=None)
            self._client = httpx.AsyncClient(timeout=120.0, transport=transport)
        return self._client

    async def close(self):
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def invoke(self, user_text: str, source_ip: str = "-") -> str:
        """
        Non-streaming: send a message and get the full response.

        Args:
            user_text: The user's message text.
            source_ip: Source IP for logging purposes.

        Returns:
            The complete response text from the agent.
        """
        client = await self._get_client()
        payload = {
            "model": self.model,
            "input": user_text,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        t0 = time.monotonic()
        try:
            resp = await client.post(self.api_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            result = self._extract_text(data)
            elapsed = time.monotonic() - t0
            traffic_logger.info(
                "inbound | src=%s | msg=%s | resp=%s | %.2fs",
                source_ip,
                _summarize(user_text),
                _summarize(result),
                elapsed,
            )
            return result
        except Exception as e:
            elapsed = time.monotonic() - t0
            traffic_logger.info(
                "inbound | src=%s | msg=%s | ERROR=%s | %.2fs",
                source_ip,
                _summarize(user_text),
                str(e),
                elapsed,
            )
            logger.error(f"OpenResponses API error: {e}")
            return f"Error calling agent: {e}"

    async def invoke_streaming(self, user_text: str) -> AsyncIterator[str]:
        """
        Streaming: send a message and yield text chunks via SSE.

        Args:
            user_text: The user's message text.

        Yields:
            Text chunks as they arrive from the API.
        """
        client = await self._get_client()
        payload = {
            "model": self.model,
            "input": user_text,
            "stream": True,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        try:
            async with client.stream(
                "POST", self.api_url, json=payload, headers=headers
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        event = json.loads(data_str)
                        text = self._extract_streaming_text(event)
                        if text:
                            yield text
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"OpenResponses streaming error: {e}")
            yield f"Error: {e}"

    @staticmethod
    def _extract_text(data: dict) -> str:
        """Extract text from OpenResponses response format."""
        output = data.get("output", [])
        texts = []
        for item in output:
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        texts.append(content.get("text", ""))
        return "\n".join(texts) if texts else str(data)

    @staticmethod
    def _extract_streaming_text(event: dict) -> str | None:
        """Extract text delta from streaming event."""
        etype = event.get("type", "")
        if etype == "response.output_text.delta":
            return event.get("delta", "")
        elif etype == "response.completed":
            return None
        return None


class OpenResponsesAgentExecutor(AgentExecutor):
    """
    A2A AgentExecutor that delegates to the OpenResponses API.

    This is the bridge between the A2A protocol and OpenClaw's API.
    It receives incoming A2A messages, forwards them to the local
    OpenResponses endpoint, and returns the response via A2A events.

    Args:
        adapter: An OpenResponsesAdapter instance for API communication.
    """

    def __init__(self, adapter: OpenResponsesAdapter):
        self.adapter = adapter

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Execute: receive A2A message, call OpenResponses, return result.

        Args:
            context: The A2A request context containing the user's message.
            event_queue: Event queue for sending back responses.
        """
        user_input = context.get_user_input()
        if not user_input:
            await event_queue.enqueue_event(
                new_agent_text_message(
                    "I didn't receive any input. Please send a message."
                )
            )
            return

        # Try to extract source IP from request context
        source_ip = "-"
        try:
            if hasattr(context, "request") and context.request:
                source_ip = (
                    getattr(context.request, "client_host", None) or "-"
                )
            elif hasattr(context, "_request") and context._request:
                source_ip = (
                    getattr(context._request, "client_host", None) or "-"
                )
        except Exception:
            pass

        logger.info(f"A2A → OpenResponses: '{user_input[:100]}...'")

        try:
            result = await self.adapter.invoke(
                user_input, source_ip=source_ip
            )
            logger.info(f"OpenResponses → A2A: '{result[:100]}...'")
            await event_queue.enqueue_event(new_agent_text_message(result))
        except Exception as e:
            logger.error(f"Execution error: {e}")
            traffic_logger.info(
                "inbound | src=%s | msg=%s | EXEC_ERROR=%s",
                source_ip,
                _summarize(user_input),
                str(e),
            )
            await event_queue.enqueue_event(
                new_agent_text_message(f"Agent execution error: {e}")
            )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel is not supported for OpenResponses calls."""
        raise Exception("Cancel not supported")
