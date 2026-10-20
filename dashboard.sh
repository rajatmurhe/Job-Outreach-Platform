#!/usr/bin/env bash
# ==============================================================================
# 🚀 Launch Pulse Outreach SaaS Control Center (FastAPI + Modern SPA)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

echo "=================================================="
echo "⚡ Launching Pulse Outreach Control Center"
echo "🌐 URL: http://localhost:5050"
echo "=================================================="

# Check if port 5050 is already running
if lsof -i :5050 >/dev/null 2>&1; then
    echo "✅ Control Center server is already running on http://localhost:5050"
    open "http://localhost:5050"
    exit 0
fi

# Open browser after a brief delay
(sleep 1 && open "http://localhost:5050") &

# Start FastAPI server
exec "$PYTHON_BIN" "$SCRIPT_DIR/server.py"
