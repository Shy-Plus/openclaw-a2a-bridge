#!/bin/bash
# ─────────────────────────────────────────────────────────
#  Install A2A Bridge as a macOS LaunchAgent
#
#  This script creates a LaunchAgent plist that:
#    - Starts the A2A server on login
#    - Automatically restarts on crash
#    - Logs output to ~/.openclaw/logs/
#
#  Usage:
#    ./install_service.sh                  # Install with defaults
#    ./install_service.sh --uninstall      # Remove the service
#
#  Environment variables:
#    A2A_LOCAL_PORT     Port (default: 9100)
#    A2A_PUBLIC_URL     Public URL for Agent Card
#    A2A_MODEL          Model name (default: openclaw:main)
#    A2A_PYTHON         Python path (default: python3)
#    A2A_AGENT_CARD     Path to agent card JSON
# ─────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LABEL="com.openclaw.a2a-bridge"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"

PYTHON="${A2A_PYTHON:-$(command -v python3.11 || command -v python3)}"
PORT="${A2A_LOCAL_PORT:-9100}"
HOST="${A2A_LOCAL_HOST:-0.0.0.0}"
PUBLIC_URL="${A2A_PUBLIC_URL:-http://${HOST}:${PORT}}"
MODEL="${A2A_MODEL:-openclaw:main}"
AGENT_CARD="${A2A_AGENT_CARD:-${PROJECT_DIR}/cards/agent_card.json}"
LOG_DIR="$HOME/.openclaw/logs"

# ─── Uninstall ────────────────────────────────────────────

if [[ "${1:-}" == "--uninstall" ]]; then
    echo "🗑  Uninstalling A2A Bridge service..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm -f "$PLIST_PATH"
    echo "✅ Service removed."
    exit 0
fi

# ─── Install ──────────────────────────────────────────────

echo "📦 Installing A2A Bridge as LaunchAgent..."
echo "   Project:    $PROJECT_DIR"
echo "   Python:     $PYTHON"
echo "   Port:       $PORT"
echo "   Public URL: $PUBLIC_URL"
echo "   Model:      $MODEL"
echo "   Agent Card: $AGENT_CARD"
echo ""

# Create log directory
mkdir -p "$LOG_DIR"

# Unload existing service if present
launchctl unload "$PLIST_PATH" 2>/dev/null || true

# Write plist
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON}</string>
        <string>-m</string>
        <string>src.server</string>
        <string>--port</string>
        <string>${PORT}</string>
        <string>--host</string>
        <string>${HOST}</string>
        <string>--model</string>
        <string>${MODEL}</string>
        <string>--agent-card</string>
        <string>${AGENT_CARD}</string>
        <string>--public-url</string>
        <string>${PUBLIC_URL}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/a2a-server.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/a2a-server.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF

# Load the service
launchctl load "$PLIST_PATH"

echo ""
echo "✅ Service installed and started!"
echo ""
echo "   Manage with:"
echo "     launchctl list | grep a2a"
echo "     launchctl unload $PLIST_PATH"
echo "     tail -f $LOG_DIR/a2a-server.log"
echo ""
echo "   Uninstall:"
echo "     $0 --uninstall"
