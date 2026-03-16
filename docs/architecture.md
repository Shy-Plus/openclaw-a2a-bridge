# Architecture

## Overview

The A2A Bridge connects OpenClaw agents running on different devices through Google's Agent-to-Agent (A2A) protocol. Each device runs an A2A server that wraps its local OpenClaw agent, making it discoverable and callable by remote agents.

## System Architecture

```
┌──────────────────────────┐                      ┌──────────────────────────┐
│     Device A             │                      │     Device B             │
│                          │                      │                          │
│  ┌────────────────────┐  │    A2A Protocol      │  ┌────────────────────┐  │
│  │    A2A Server       │◄─┼── (JSON-RPC/HTTP) ──┼─►│    A2A Server       │  │
│  │    (port 9100)      │  │    over Tailscale    │  │    (port 9100)      │  │
│  └────────┬───────────┘  │                      │  └────────┬───────────┘  │
│           │               │                      │           │               │
│           ▼               │                      │           ▼               │
│  ┌────────────────────┐  │                      │  ┌────────────────────┐  │
│  │ OpenResponses       │  │                      │  │ OpenResponses       │  │
│  │ Adapter             │  │                      │  │ Adapter             │  │
│  └────────┬───────────┘  │                      │  └────────┬───────────┘  │
│           │               │                      │           │               │
│           ▼               │                      │           ▼               │
│  ┌────────────────────┐  │                      │  ┌────────────────────┐  │
│  │ OpenResponses API   │  │                      │  │ OpenResponses API   │  │
│  │ (port 18789)        │  │                      │  │ (port 18789)        │  │
│  └────────┬───────────┘  │                      │  └────────┬───────────┘  │
│           │               │                      │           │               │
│           ▼               │                      │           ▼               │
│  ┌────────────────────┐  │                      │  ┌────────────────────┐  │
│  │ OpenClaw Agent      │  │                      │  │ OpenClaw Agent      │  │
│  └────────────────────┘  │                      │  └────────────────────┘  │
└──────────────────────────┘                      └──────────────────────────┘
```

## Component Details

### A2A Server (`src/server.py`)

The A2A server is the external-facing component. It:

1. **Loads the Agent Card** — Defines the agent's identity, capabilities, and skills
2. **Exposes discovery endpoint** — `GET /.well-known/agent.json` returns the Agent Card
3. **Handles JSON-RPC requests** — Receives messages via the A2A protocol
4. **Supports streaming** — SSE (Server-Sent Events) for real-time responses

Built on the official `a2a-sdk` Python library and Starlette for HTTP handling.

### OpenResponses Adapter (`src/adapter.py`)

The adapter is the core bridge between A2A and OpenClaw:

1. **Receives A2A messages** — From the `AgentExecutor` interface
2. **Translates to OpenResponses API calls** — Maps A2A message format to OpenClaw's API
3. **Handles responses** — Extracts text from API responses and returns via A2A events
4. **Traffic logging** — All requests/responses are logged to rotating log files

### A2A Client (`src/client.py`)

The client enables outbound communication:

1. **Agent discovery** — Fetches and validates remote Agent Cards
2. **Message sending** — Both synchronous and streaming modes
3. **Interactive mode** — Terminal-based chat with context persistence

### Configuration (`src/config.py`)

Centralized configuration with environment variable overrides:

- Network settings (hosts, ports, URLs)
- Authentication tokens
- Agent card paths
- Logging configuration

## Data Flow

### Inbound Request (Remote Agent → Local Agent)

```
Remote A2A Client
    │
    ▼ HTTP POST / (JSON-RPC)
A2A Server (Starlette)
    │
    ▼ AgentExecutor.execute()
OpenResponses Adapter
    │
    ▼ POST /v1/responses
OpenResponses API (OpenClaw Gateway)
    │
    ▼ Agent processes message
Response flows back through the same chain
```

### Agent Discovery

```
Any A2A Client
    │
    ▼ GET /.well-known/agent.json
A2A Server
    │
    ▼ Returns AgentCard JSON
Client now knows:
  - Agent name and description
  - Available skills
  - Supported capabilities
  - Communication URL
```

## Network Architecture

The bridge is designed for **Tailscale** mesh networks:

- Each device has a stable Tailscale IP (100.x.x.x)
- Traffic is end-to-end encrypted by Tailscale
- No need to expose ports to the public internet
- Works across NATs, firewalls, and different networks

Alternative network setups:
- **Local network**: Use LAN IPs directly
- **Cloud**: Use public IPs or reverse proxy
- **ngrok/Cloudflare Tunnel**: For public access without port forwarding

## Security Model

1. **Network layer**: Tailscale provides end-to-end encryption
2. **Application layer**: Bearer token authentication for the OpenResponses API
3. **Agent Cards**: Contain no sensitive information
4. **Traffic logs**: Stored locally, never transmitted
