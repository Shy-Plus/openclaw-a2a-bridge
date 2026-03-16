# OpenClaw A2A Bridge Install Prompt

Language: [中文](INSTALL_PROMPT.md) | **English**

Copy the entire block below and send it to your own OpenClaw agent. It will handle the installation, configuration, and connection automatically.

```text
You need to install OpenClaw A2A Bridge so my agent can communicate with agents on other devices via Google's A2A protocol.

Your goal is not to explain — just get it installed, configured, and running.

Strict constraints:
1. Do not modify openclaw.json except to enable OpenResponses API (gateway.http.endpoints.responses.enabled = true).
2. Do not fabricate any API keys or tokens. The Gateway token is auto-read from openclaw.json.
3. Do not assume fixed IP addresses. Detect the actual machine IP.
4. All sensitive values go through environment variables, never hardcoded.
5. If any dependency fails to install, stop and tell me why. Do not skip.

Execute in this order:

Phase 1: Environment Check
1. Confirm Python 3.11+ is available:
   - `python3.11 --version` or `python3 --version`
   - If missing, tell me the install command (brew install python@3.11 / apt install python3.11)
2. Confirm OpenClaw Gateway is reachable:
   - `openclaw status` or `curl -sS http://localhost:18789/health`
   - Record the Gateway port (default 18789)
3. Check OpenResponses API status:
   - Check if gateway.http.endpoints.responses.enabled is true in openclaw.json
   - If not, enable it via gateway config.patch tool and restart the gateway
4. Detect machine IP (by priority):
   - Tailscale IP: `tailscale status` or `tailscale ip -4` (if tailscale is installed)
   - LAN IP: `ipconfig getifaddr en0` (macOS) or `hostname -I` (Linux)
   - Record as MY_IP for A2A_PUBLIC_URL
5. Confirm pip is available: `python3.11 -m pip --version`

Phase 2: Install
6. Choose install directory (by priority):
   - If OpenClaw workspace exists: `~/.openclaw/workspace/projects/a2a-bridge/`
   - Otherwise: `~/projects/a2a-bridge/`
7. Clone the repo:
   ```bash
   git clone https://github.com/Shy-Plus/openclaw-a2a-bridge.git <install-dir>
   cd <install-dir>
   ```
8. If the directory already exists, `git pull` to update instead of re-cloning.
9. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   If pip install fails (network issues), try:
   ```bash
   pip install 'a2a-sdk[http-server]' httpx uvicorn
   ```

Phase 3: Configure
10. Create config from template:
    ```bash
    cp .env.example .env
    ```
11. Modify these values in .env (keep others as default):
    - `A2A_PUBLIC_URL=http://{MY_IP}:9100` (use the IP detected in Phase 1)
    - `A2A_LOCAL_API=http://localhost:{GATEWAY_PORT}/v1/responses` (use the port from Phase 1)
    - Leave `A2A_GATEWAY_TOKEN` empty (auto-reads from openclaw.json)
12. Customize the Agent Card (important — this is your agent's "business card"):
    - Edit `cards/agent_card.json`
    - Change `name` to your agent's name
    - Change `description` to describe your agent
    - Update `skills` array to describe what your agent can do
    - Change `provider.organization` to your org/name
13. Create log directories:
    ```bash
    mkdir -p ~/.openclaw/workspace/logs/
    mkdir -p ~/.openclaw/logs/
    ```

Phase 4: Start and Verify
14. Start the A2A Server:
    ```bash
    ./scripts/run_server.sh
    ```
    Or manually:
    ```bash
    python -m src.server --port 9100 --public-url http://{MY_IP}:9100
    ```
15. Verify Agent Card is reachable:
    ```bash
    curl -sS http://localhost:9100/.well-known/agent-card.json
    ```
    Should return your agent card JSON.
16. Verify external reachability (if you have another machine):
    ```bash
    curl -sS http://{MY_IP}:9100/.well-known/agent-card.json
    ```
17. Run health check:
    ```bash
    python -m src.health_check --url http://localhost:9100
    ```
    Should show 3/3 green (A2A Server / Agent Card / OpenResponses API).

Phase 5: Connect to Remote Agent (optional)
18. If you know a remote agent's A2A address, test discovery:
    ```bash
    python -m src.client --target http://{REMOTE_IP}:9100 --discover-only
    ```
    Should show the remote agent's card and skills.
19. Send a test message:
    ```bash
    python -m src.client --target http://{REMOTE_IP}:9100 --message "Hello, my A2A Bridge is set up!"
    ```
20. If the remote agent replies, bidirectional A2A communication is established.

Phase 6: Auto-Start (optional but recommended)
21. macOS:
    ```bash
    ./scripts/install_service.sh
    ```
    Creates a LaunchAgent for auto-start on boot with crash recovery.
22. Linux (systemd):
    See docs/setup-guide.md for systemd configuration.
23. Verify the service:
    ```bash
    ./scripts/run_server.sh status
    ```

Phase 7: Deliver Results
24. After installation, output:
    - ✅ or ❌: Result of each phase
    - Local A2A address: http://{MY_IP}:9100
    - Agent Card URL: http://{MY_IP}:9100/.well-known/agent-card.json
    - Agent name and number of skills
    - Whether a remote agent was connected (if applicable)
    - Whether auto-start was configured
    - Log file locations
    - If any step failed: cause and fix suggestion

Common issue handling:
- If port 9100 is in use, try 9200 or another free port, and update .env
- If Tailscale is not installed, use LAN IP; if machines are on different networks, set up connectivity first
- If pip install times out, try a mirror: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
- If OpenResponses API returns 401, check the gateway auth token
- If Agent Card URL contains 127.0.0.1, confirm A2A_PUBLIC_URL is set to an externally reachable IP
```
