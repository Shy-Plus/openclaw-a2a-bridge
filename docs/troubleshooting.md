# Troubleshooting

## Common Issues

### A2A Server won't start

**Symptom:** Server exits immediately or shows an error.

1. **Check port availability:**
   ```bash
   lsof -i :9100
   ```
   If something is using port 9100, either stop it or use `--port 9200`.

2. **Verify Python version:**
   ```bash
   python3 --version  # Must be 3.11+
   ```

3. **Check dependencies:**
   ```bash
   python3 -c "import a2a; print(a2a.__version__)"
   ```
   If this fails, reinstall: `pip install -r requirements.txt`

4. **Check gateway token:**
   ```bash
   # Token should be non-empty
   python3 -c "from src.config import GATEWAY_TOKEN; print('Token:', 'set' if GATEWAY_TOKEN else 'MISSING')"
   ```

### Agent Card returns error

**Symptom:** `curl http://host:9100/.well-known/agent.json` fails.

1. **Verify the server is running:**
   ```bash
   curl -v http://localhost:9100/.well-known/agent.json
   ```

2. **Check agent card JSON syntax:**
   ```bash
   python3 -c "import json; json.load(open('cards/agent_card.json'))"
   ```

3. **Ensure the URL in agent card matches your public URL:**
   The `url` field in the agent card is overridden at runtime by `--public-url`.

### Connection timeout between devices

**Symptom:** Client hangs when connecting to a remote agent.

1. **Check network connectivity:**
   ```bash
   ping REMOTE_IP
   ```

2. **Check Tailscale status (if using Tailscale):**
   ```bash
   tailscale status
   ```

3. **Verify the remote server is listening:**
   ```bash
   # On the remote machine
   lsof -i :9100
   ```

4. **Check for proxy interference:**
   The bridge bypasses system proxies by default, but check:
   ```bash
   echo $http_proxy $HTTP_PROXY
   ```

### OpenResponses API unreachable

**Symptom:** Agent card works but messages return errors.

1. **Check if OpenClaw gateway is running:**
   ```bash
   curl -s http://localhost:18789/v1/responses \
     -X POST \
     -H 'Content-Type: application/json' \
     -d '{"model":"echo","input":"test"}'
   ```

2. **Verify the API URL in config:**
   ```bash
   python3 -c "from src.config import LOCAL_API_URL; print(LOCAL_API_URL)"
   ```

3. **Check gateway auth:**
   If you get 401 errors, your token may be wrong. Re-check `A2A_GATEWAY_TOKEN` or `~/.openclaw/openclaw.json`.

### Streaming not working

**Symptom:** Regular messages work, but `--stream` hangs.

1. Verify your OpenResponses API supports streaming
2. Check if there's a reverse proxy that buffers SSE responses
3. Try with a longer timeout: the bridge uses 120s by default

### LaunchAgent won't start (macOS)

**Symptom:** Service doesn't run after login.

1. **Validate plist syntax:**
   ```bash
   plutil -lint ~/Library/LaunchAgents/com.openclaw.a2a-bridge.plist
   ```

2. **Check launchd logs:**
   ```bash
   tail -50 ~/.openclaw/logs/a2a-server.log
   ```

3. **Reload the service:**
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.openclaw.a2a-bridge.plist
   launchctl load ~/Library/LaunchAgents/com.openclaw.a2a-bridge.plist
   ```

4. **Check service status:**
   ```bash
   launchctl list | grep a2a
   ```

## Health Check

The built-in health check validates all components:

```bash
# Check local
python -m src.health_check

# Check a specific URL
python -m src.health_check --url http://remote:9100

# JSON output for scripting
python -m src.health_check --json
```

## Traffic Logs

All A2A traffic is logged to `~/.openclaw/logs/a2a-traffic.log`:

```bash
# Watch live traffic
tail -f ~/.openclaw/logs/a2a-traffic.log

# Check recent entries
tail -20 ~/.openclaw/logs/a2a-traffic.log
```

Log format:
```
2026-03-16 19:00:00 | inbound | src=100.x.x.x | msg=Hello | resp=Hi there! | 2.35s
```

If logs aren't being written:
1. Ensure the log directory exists: `mkdir -p ~/.openclaw/logs/`
2. Check file permissions
3. Send a test message and check again

## Getting Help

- **GitHub Issues:** https://github.com/Shy-Plus/openclaw-a2a-bridge/issues
- **OpenClaw:** https://github.com/nicepkg/openclaw
- **A2A Protocol:** https://github.com/a2aproject/A2A
