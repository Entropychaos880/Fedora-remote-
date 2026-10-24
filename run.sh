#!/usr/bin/env bash
# run.sh - Start Fedora Remote Trackpad Server
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

# Check if /dev/uinput is writable
if [ ! -w /dev/uinput ]; then
    # If the user belongs to input group in /etc/group but not in current shell session
    if getent group input | grep -q "\b$USER\b" && [ -z "$ALREADY_TRIED_SG" ]; then
        export ALREADY_TRIED_SG=1
        exec sg input -c "$0 $*"
    fi

    echo "⚠️ Warning: /dev/uinput is not writable by current user ($USER)."
    echo "You can either:"
    echo "  1) Run setup once:   sudo ./setup_uinput.sh"
    echo "  2) Run with sudo:     sudo .venv/bin/python server.py"
    echo ""
    echo "Attempting to run anyway..."
fi

exec .venv/bin/python3 server.py "$@"
