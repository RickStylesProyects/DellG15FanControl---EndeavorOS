#!/bin/bash
# Dell G15 Fan Control - Launcher Script
# This wrapper handles running the GUI with proper display access

# Resolve symlinks to get the real script directory
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

# Export display variables for sudo
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# For Wayland
if [ -n "$WAYLAND_DISPLAY" ]; then
    export QT_QPA_PLATFORM=wayland
fi

# Run with sudo (will use sudoers rule for passwordless if configured)
# Preserving display environment variables with -E
sudo -E /usr/bin/python3 "$SCRIPT_DIR/g15_fan_control.py" "$@"
