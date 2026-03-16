# Setup Guide

## Prerequisites

- **Python 3.11+** — The bridge requires Python 3.11 or newer
- **OpenClaw** — An OpenClaw instance running with the OpenResponses API enabled
- **Network connectivity** — Either Tailscale, local network, or any IP-reachable setup

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Shy-Plus/openclaw-a2a-bridge.git
cd openclaw-a2a-bridge
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install -e .
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Key settings to configure:

| Variable | What to set |
|----------|------------|
| `A2A_GATEWAY_TOKEN` | Your OpenClaw gateway token (or leave empty to auto-detect from `~/.openclaw/openclaw.json`) |
| `A2A_PUBLIC_URL` | The URL other agents will use to reach this server (e.g., `http://YOUR_TAILSCALE_IP:9100`) |
| `A2A_LOCAL_PORT` | Port for the A2A server (default: 9100) |

### 4. Customize your Agent Card

Edit `cards/agent_card.json` to describe your agent:

```json
{
  "name": "My Agent",
  "description": "A brief description of what your agent does",
  "skills": [
    {
      "id": "unique_skill_id",
      "name": "Skill Name",
      "description": "What this skill does",
      "tags": ["tag1", "tag2"],
      "examples": ["Example prompt 1", "Example prompt 2"]
    }
  ]
}
```

### 5. Start the server

```bash
# Using the script
./scripts/run_server.sh

# Or directly
python -m src.server --port 9100 --public-url http://YOUR_IP:9100
```

### 6. Verify it's working

```bash
# Check the Agent Card
curl http://localhost:9100/.well-known/agent.json

# Run health check
python -m src.health_check --url http://localhost:9100

# Send a test message from another machine
python -m src.client --target http://YOUR_IP:9100 --message "Hello!"
```

## Multi-Device Setup

### Setting up Device A (Primary)

1. Install and configure as above
2. Note your Tailscale IP: `tailscale ip -4`
3. Start the server: `./scripts/run_server.sh`

### Setting up Device B (Secondary)

1. Install and configure on the second device
2. Set `A2A_PUBLIC_URL` to Device B's Tailscale IP
3. Use `cards/remote_agent_card.json` as your agent card (customize it)
4. Start: `./scripts/run_server.sh --agent-card cards/remote_agent_card.json`

### Test connectivity

From Device A:
```bash
python -m src.client --target http://DEVICE_B_IP:9100 --discover-only
```

From Device B:
```bash
python -m src.client --target http://DEVICE_A_IP:9100 --discover-only
```

## Auto-Start on Boot (macOS)

Use the provided install script:

```bash
# Install as LaunchAgent
./scripts/install_service.sh

# Uninstall
./scripts/install_service.sh --uninstall
```

This creates a macOS LaunchAgent that:
- Starts the server on login
- Restarts automatically if it crashes
- Logs to `~/.openclaw/logs/a2a-server.log`

## Auto-Start on Boot (Linux)

Create a systemd service:

```bash
sudo cat > /etc/systemd/system/a2a-bridge.service << 'EOF'
[Unit]
Description=OpenClaw A2A Bridge
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/openclaw-a2a-bridge
ExecStart=/usr/bin/python3 -m src.server --port 9100
Restart=always
RestartSec=10
EnvironmentFile=/path/to/openclaw-a2a-bridge/.env

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable a2a-bridge
sudo systemctl start a2a-bridge
```

## Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9100
CMD ["python", "-m", "src.server", "--port", "9100"]
```

```bash
docker build -t a2a-bridge .
docker run -d --name a2a-bridge \
  -p 9100:9100 \
  -e A2A_GATEWAY_TOKEN=your_token \
  -e A2A_PUBLIC_URL=http://your-ip:9100 \
  a2a-bridge
```
