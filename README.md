# 🌉 OpenClaw A2A Bridge

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![A2A Protocol](https://img.shields.io/badge/A2A-Protocol-orange.svg)](https://github.com/a2aproject/A2A)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-compatible-purple.svg)](https://github.com/nicepkg/openclaw)

**Cross-device Agent-to-Agent communication bridge for [OpenClaw](https://github.com/nicepkg/openclaw), powered by [Google's A2A Protocol](https://github.com/a2aproject/A2A).**

> Your AI agents shouldn't be islands. This bridge lets them talk to each other — across devices, across networks, speaking a standard protocol.

---

## Why This Project?

AI agents are powerful individually, but **collaboration** unlocks their real potential. The problem? Most agent frameworks trap agents in single-machine silos.

**OpenClaw A2A Bridge** solves this by implementing Google's A2A protocol — the emerging standard for agent interoperability — on top of OpenClaw's powerful agent runtime. Now your agents can:

- 🔍 **Discover** each other's capabilities automatically
- 💬 **Communicate** via a standard JSON-RPC protocol
- 🌐 **Collaborate** across devices on your Tailscale network (or any network)
- 🔄 **Stream** responses in real-time via SSE

## Features

| Feature | Description |
|---------|-------------|
| **A2A Protocol Compliance** | Full implementation of Agent Card discovery, JSON-RPC 2.0 messaging, and SSE streaming |
| **OpenClaw Integration** | Wraps any OpenClaw agent as an A2A-compliant service via the OpenResponses API |
| **Cross-Device** | Designed for multi-machine setups with Tailscale, but works on any network |
| **Zero Config Discovery** | Agents self-describe via `/.well-known/agent.json` — no registry needed |
| **Traffic Logging** | All A2A traffic logged with rotation for debugging and monitoring |
| **Health Checks** | Built-in health check for all components (server, agent card, API) |
| **Auto-Start** | LaunchAgent (macOS) and systemd (Linux) support included |
| **Interactive Client** | CLI client with discovery, one-shot, streaming, and interactive modes |

## Architecture

```
┌──────────────────────┐          A2A Protocol          ┌──────────────────────┐
│    Device A           │       (JSON-RPC / HTTP)        │    Device B           │
│                       │                                │                       │
│  ┌─────────────────┐  │  ◄───── Tailscale / LAN ────► │  ┌─────────────────┐  │
│  │  A2A Server      │  │         or any network        │  │  A2A Server      │  │
│  │  (port 9100)     │  │                                │  │  (port 9100)     │  │
│  └────────┬────────┘  │                                │  └────────┬────────┘  │
│           │            │                                │           │            │
│           ▼            │                                │           ▼            │
│  ┌─────────────────┐  │                                │  ┌─────────────────┐  │
│  │  OpenResponses   │  │                                │  │  OpenResponses   │  │
│  │  Adapter         │  │                                │  │  Adapter         │  │
│  └────────┬────────┘  │                                │  └────────┬────────┘  │
│           │            │                                │           │            │
│           ▼            │                                │           ▼            │
│  ┌─────────────────┐  │                                │  ┌─────────────────┐  │
│  │  OpenClaw Agent  │  │                                │  │  OpenClaw Agent  │  │
│  └─────────────────┘  │                                │  └─────────────────┘  │
└──────────────────────┘                                └──────────────────────┘
```

## Quick Start

### 1. Install

```bash
git clone https://github.com/Shy-Plus/openclaw-a2a-bridge.git
cd openclaw-a2a-bridge
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — at minimum, set A2A_PUBLIC_URL to your machine's IP
```

### 3. Run

```bash
# Start the server
./scripts/run_server.sh

# Or directly:
python -m src.server --port 9100 --public-url http://YOUR_IP:9100
```

That's it. Your agent is now discoverable via A2A at `http://YOUR_IP:9100/.well-known/agent.json`.

## Usage

### Discover a remote agent

```bash
python -m src.client --target http://remote-agent:9100 --discover-only
```

```
🤖 Agent: Remote Agent
   Version: 1.0.0
   Skills (3):
     • General Conversation: Engage in natural conversation
     • Creative Assistant: Help with creative tasks
     • Frontend Development: React, Next.js, CSS, UI/UX
```

### Send a message

```bash
python -m src.client --target http://remote-agent:9100 -m "Explain the A2A protocol"
```

### Interactive chat

```bash
python -m src.client --target http://remote-agent:9100
```

### Streaming mode

```bash
python -m src.client --target http://remote-agent:9100 -m "Tell me a story" --stream
```

### Health check

```bash
python -m src.health_check --url http://localhost:9100
```

```
✅ http://localhost:9100 — HEALTHY
   ✅ A2A Server: 12ms
   ✅ Agent Card: 8ms — My Agent v1.0.0 (3 skills)
   ✅ OpenResponses API: 45ms
```

### Run the collaboration demo

```bash
# Start servers on both machines first, then:
python examples/demo.py --local http://agent-a:9100 --remote http://agent-b:9100
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `A2A_GATEWAY_TOKEN` | Auto-detect from `openclaw.json` | Gateway auth token |
| `A2A_LOCAL_HOST` | `0.0.0.0` | Server bind address |
| `A2A_LOCAL_PORT` | `9100` | Server port |
| `A2A_LOCAL_API` | `http://localhost:18789/v1/responses` | OpenResponses API URL |
| `A2A_PUBLIC_URL` | `http://{host}:{port}` | URL advertised in Agent Card |
| `A2A_REMOTE_HOST` | — | Remote agent IP (for multi-agent) |
| `A2A_REMOTE_PORT` | `9100` | Remote agent port |
| `A2A_MODEL` | `openclaw:main` | Model for OpenResponses API |
| `A2A_AGENT_CARD` | `cards/agent_card.json` | Agent card file path |
| `A2A_TRAFFIC_LOG` | `~/.openclaw/logs/a2a-traffic.log` | Traffic log path |

### Agent Card

The Agent Card (`cards/agent_card.json`) defines your agent's identity and capabilities. Customize it to describe what your agent can do:

```json
{
  "name": "My Agent",
  "description": "What this agent does",
  "skills": [
    {
      "id": "skill_id",
      "name": "Skill Name",
      "description": "What this skill does",
      "tags": ["tag1"],
      "examples": ["Example prompt"]
    }
  ]
}
```

## A2A Protocol Compliance

| A2A Feature | Status | Notes |
|-------------|--------|-------|
| Agent Card (Discovery) | ✅ | `GET /.well-known/agent.json` |
| JSON-RPC 2.0 | ✅ | Full request/response cycle |
| Synchronous messaging | ✅ | Standard request → response |
| SSE Streaming | ✅ | Real-time token streaming |
| Multi-skill declaration | ✅ | Via Agent Card skills array |
| Bearer Token Auth | ✅ | For OpenResponses API |
| Task management | ✅ | In-memory task store |

## Project Structure

```
openclaw-a2a-bridge/
├── src/
│   ├── __init__.py          # Package init
│   ├── server.py            # A2A server (Starlette + uvicorn)
│   ├── client.py            # A2A client (discovery + messaging)
│   ├── adapter.py           # OpenResponses ↔ A2A bridge
│   ├── config.py            # Centralized configuration
│   └── health_check.py      # Component health checker
├── cards/
│   ├── agent_card.json      # Primary agent card (customize this)
│   └── remote_agent_card.json # Example remote agent card
├── scripts/
│   ├── run_server.sh        # Start/stop/restart/status
│   └── install_service.sh   # macOS LaunchAgent installer
├── examples/
│   ├── demo.py              # Multi-agent collaboration demo
│   └── collaborative_workflow.py  # Pipeline workflow example
├── docs/
│   ├── architecture.md      # Detailed architecture docs
│   ├── setup-guide.md       # Step-by-step setup guide
│   └── troubleshooting.md   # Common issues & solutions
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
├── setup.py                 # pip install support
└── LICENSE                  # MIT License
```

## Auto-Start

### macOS (LaunchAgent)

```bash
./scripts/install_service.sh          # Install
./scripts/install_service.sh --uninstall  # Remove
```

### Linux (systemd)

See [docs/setup-guide.md](docs/setup-guide.md#auto-start-on-boot-linux) for systemd setup.

## Contributing

Contributions welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit changes: `git commit -m "feat: add my feature"`
4. Push: `git push origin feat/my-feature`
5. Open a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

## License

[MIT License](LICENSE) — use it however you want.

## Credits

- **[Google A2A Protocol](https://github.com/a2aproject/A2A)** — The Agent-to-Agent protocol specification
- **[a2a-sdk](https://pypi.org/project/a2a-sdk/)** — Official Python SDK for A2A
- **[OpenClaw](https://github.com/nicepkg/openclaw)** — The AI agent runtime this bridge extends
- **[Tailscale](https://tailscale.com/)** — Mesh VPN for secure cross-device connectivity

---

<p align="center">
  Built by <a href="https://github.com/Shy-Plus">Shy's Lab</a> 🪐
  <br>
  <sub>Making agents talk to each other, one bridge at a time.</sub>
</p>
