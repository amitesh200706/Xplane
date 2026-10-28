#!/usr/bin/env bash
# File Cache App launcher — opens the GUI.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 &>/dev/null; then
    exec python3 "$SCRIPT_DIR/app.py"
elif command -v python &>/dev/null; then
    exec python "$SCRIPT_DIR/app.py"
else
    echo "Python is not installed. Install Python 3.10+ and try again." >&2
    exit 1
fi
