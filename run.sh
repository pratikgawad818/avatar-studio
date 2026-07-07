#!/bin/bash
# Avatar Studio — Start server
set -e

STUDIO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$STUDIO_DIR/venv"
PYTHON="$VENV/bin/python3"

# Checks
if [ ! -d "$VENV" ]; then
  echo "ERROR: venv not found at $VENV"
  echo "Run: python3 -m venv venv && source venv/bin/activate && pip install fastapi uvicorn[standard] python-multipart"
  exit 1
fi

if [ ! -f "$PYTHON" ]; then
  PYTHON="$VENV/bin/python"
  if [ ! -f "$PYTHON" ]; then
    echo "ERROR: No python3 found in venv/bin/"
    exit 1
  fi
fi

# Kill anything already on port 8002
lsof -ti:8002 | xargs kill -9 2>/dev/null || true

# Fix: empty PYTHONHASHSEED breaks Wav2Lip subprocess
unset PYTHONHASHSEED

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║        Avatar Studio — v1.0           ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""
echo "  Open → http://localhost:8002"
echo "  Stop → Ctrl+C"
echo ""

cd "$STUDIO_DIR"
exec "$PYTHON" -m uvicorn app:app --host 0.0.0.0 --port 8002 --reload
