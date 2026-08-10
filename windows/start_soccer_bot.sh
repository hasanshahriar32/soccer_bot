#!/bin/bash
# ====================================================================
#            SOCCER BOT ROBOTICS LAUNCHER (LINUX & WSL)
# ====================================================================

echo "===================================================================="
echo "             SOCCER BOT ROBOTICS SYSTEM (LINUX / WSL)"
echo "===================================================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
python3 "$SCRIPT_DIR/launch_windows_hub.py"
