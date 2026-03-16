#!/bin/bash
# ─────────────────────────────────────────────────────────
#  A2A Bridge Server — Start/Stop/Status Script
#
#  Usage:
#    ./run_server.sh              # Start the A2A server
#    ./run_server.sh stop         # Stop the server
#    ./run_server.sh restart      # Restart the server
#    ./run_server.sh status       # Check if running
#    ./run_server.sh --port 9200  # Custom port
# ─────────────────────────────────────────────────────────

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

PYTHON="${A2A_PYTHON:-python3}"
PORT="${A2A_LOCAL_PORT:-9100}"
HOST="${A2A_LOCAL_HOST:-0.0.0.0}"
PUBLIC_URL="${A2A_PUBLIC_URL:-http://${HOST}:${PORT}}"
MODEL="${A2A_MODEL:-openclaw:main}"
AGENT_CARD="${A2A_AGENT_CARD:-${PROJECT_DIR}/cards/agent_card.json}"
SUBCOMMAND=""

# ─── Functions ────────────────────────────────────────────

find_pid() {
    pgrep -f "python.*src.server" 2>/dev/null || \
    pgrep -f "python.*server.py" 2>/dev/null || true
}

do_status() {
    local pid
    pid=$(find_pid)
    if [[ -n "$pid" ]]; then
        echo "✅ A2A Server is running (PID: $pid)"
        echo "   Port: $(lsof -iTCP -sTCP:LISTEN -P -n 2>/dev/null | grep "$pid" | awk '{print $9}' | head -1 || echo "$PORT")"
        return 0
    else
        echo "❌ A2A Server is not running"
        return 1
    fi
}

do_stop() {
    local pid
    pid=$(find_pid)
    if [[ -n "$pid" ]]; then
        echo "⏹  Stopping A2A Server (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        echo "✅ Stopped."
    else
        echo "ℹ️  A2A Server is not running."
    fi
}

do_start() {
    local existing_pid
    existing_pid=$(find_pid)
    if [[ -n "$existing_pid" ]]; then
        echo "⚠️  A2A Server already running (PID: $existing_pid)"
        echo "   Use './run_server.sh restart' to restart."
        exit 1
    fi

    echo "╔════════════════════════════════════════════════╗"
    echo "║          A2A Bridge Server                     ║"
    echo "╠════════════════════════════════════════════════╣"
    echo "║  Agent Card: $AGENT_CARD"
    echo "║  Host:       $HOST:$PORT"
    echo "║  Public URL: $PUBLIC_URL"
    echo "║  Model:      $MODEL"
    echo "║  Python:     $PYTHON"
    echo "╚════════════════════════════════════════════════╝"
    echo ""

    # Check Python
    if ! command -v "$PYTHON" &>/dev/null; then
        echo "❌ Python not found: $PYTHON"
        echo "   Set A2A_PYTHON env var or install Python 3.11+"
        exit 1
    fi

    # Check dependencies
    $PYTHON -c "import a2a" 2>/dev/null || {
        echo "❌ a2a-sdk not installed. Run:"
        echo "   $PYTHON -m pip install 'a2a-sdk[http-server]' httpx"
        exit 1
    }

    # Start server
    cd "$PROJECT_DIR"
    exec "$PYTHON" -m src.server \
        --host "$HOST" \
        --port "$PORT" \
        --agent-card "$AGENT_CARD" \
        --model "$MODEL" \
        --public-url "$PUBLIC_URL"
}

# ─── Parse args ───────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case $1 in
        start)   SUBCOMMAND="start";   shift ;;
        stop)    SUBCOMMAND="stop";    shift ;;
        restart) SUBCOMMAND="restart"; shift ;;
        status)  SUBCOMMAND="status";  shift ;;
        --port)       PORT="$2";       shift 2 ;;
        --host)       HOST="$2";       shift 2 ;;
        --model)      MODEL="$2";      shift 2 ;;
        --public-url) PUBLIC_URL="$2"; shift 2 ;;
        --agent-card) AGENT_CARD="$2"; shift 2 ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [start|stop|restart|status] [--port N] [--model M] [--public-url URL] [--agent-card PATH]"
            exit 1
            ;;
    esac
done

# ─── Execute subcommand ──────────────────────────────────

case "${SUBCOMMAND:-start}" in
    start)   do_start   ;;
    stop)    do_stop    ;;
    restart) do_stop; sleep 1; do_start ;;
    status)  do_status  ;;
esac
