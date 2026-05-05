#!/usr/bin/env bash
set -euo pipefail

exec tmux display-popup -E -w 40% -h 40% -T "Claude Watcher" \
  python3 ~/.config/tmux/scripts/claude_watcher.py tui
