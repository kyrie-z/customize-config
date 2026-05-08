#!/usr/bin/env python3
"""Claude Watcher - Track Claude Code sessions in tmux."""

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Paths
STATE_FILE = Path("/tmp/claude-watcher-state.json")
LOCK_FILE = Path("/tmp/claude-watcher-state.lock")
LOG_FILE = Path("/tmp/claude-watcher.log")

# Status icons
STATUS_ICONS = {
    "running": "🤖",
    "completed": "✅",
    "idle": "💤",
}


def log(hook_name: str, message: str):
    """Write log message with timestamp and hook name."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} [{hook_name}] {message}\n")


def run_tmux(*args: str) -> str:
    """Run tmux command and return output."""
    try:
        result = subprocess.run(
            ["tmux"] + list(args),
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def get_process_tree_pids(pid: int) -> set[int]:
    """Get all PIDs in the process tree of given PID."""
    pids = {pid}
    try:
        result = subprocess.run(
            ["ps", "--ppid", str(pid), "-o", "pid=", "--no-headers"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                child_pid = int(line.strip())
                pids.update(get_process_tree_pids(child_pid))
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        pass
    return pids


def find_pane_by_pid(claude_pid: int) -> Optional[tuple[str, str, str]]:
    """Find tmux pane containing Claude process by PID.

    Returns (session_id, window_id, pane_id) or None.
    """
    output = run_tmux("list-panes", "-a", "-F", "#{session_id} #{window_id} #{pane_id} #{pane_pid}")
    if not output:
        return None

    claude_tree = get_process_tree_pids(claude_pid)

    for line in output.split("\n"):
        parts = line.strip().split()
        if len(parts) != 4:
            continue
        session_id, window_id, pane_id, pane_pid_str = parts
        try:
            pane_pid = int(pane_pid_str)
            if pane_pid in claude_tree or claude_pid in get_process_tree_pids(pane_pid):
                return (session_id, window_id, pane_id)
        except ValueError:
            continue
    return None


def get_last_prompt(pane_id: str) -> str:
    """Extract recent user message from pane content as task summary."""
    content = run_tmux("capture-pane", "-t", pane_id, "-p", "-S", "-300")
    if not content:
        return ""

    lines = content.split("\n")

    # Skip patterns for status/info lines
    skip_patterns = [
        r"^(In:|Out:|Cache|GLM|Context|Session|Running)",
        r"[↓↑]\s*\d+\s*tokens",
        r"\d+s\s*[··]",
        r"^─+",
        r"^╭|^╰",
        r"accept edits",
        r"shift\+tab",
        r"^\s*\$",
        r"^Next:",
        r"^✶\s+实现",
        r"^✽\s+实现",
    ]

    # Look for user input patterns (Chinese or meaningful text)
    for line in reversed(lines):
        line = line.strip()
        if not line or len(line) < 5:
            continue

        # Skip status/info lines
        should_skip = False
        for pattern in skip_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                should_skip = True
                break
        if should_skip:
            continue

        # Skip lines that start with special characters
        if line.startswith(("⎿", "✶", "✽", "❯", "$ ", "●", "○", "◦", "⏺")):
            continue

        # Skip if line is mostly special chars
        special_chars = sum(1 for c in line if c in "─╭╰│├┤┬┴┼⎿✶✽❯●○◦⏺")
        if special_chars > len(line) * 0.3:
            continue

        # Check if line has Chinese characters or looks like a question/task
        has_chinese = bool(re.search(r"[一-鿿]", line))
        is_question = "?" in line or "？" in line
        is_long = len(line) > 10

        if has_chinese or is_question or is_long:
            return line[:80]

    return ""


def with_lock(func):
    """Decorator to acquire file lock before operation."""
    def wrapper(*args, **kwargs):
        with open(LOCK_FILE, "w") as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
            try:
                return func(*args, **kwargs)
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
    return wrapper


def load_state() -> dict:
    """Load state from JSON file."""
    if not STATE_FILE.exists():
        return {"sessions": {}, "updated_at": ""}
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return {"sessions": {}, "updated_at": ""}


def save_state(state: dict):
    """Save state to JSON file."""
    state["updated_at"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def make_key(session_id: str, window_id: str, pane_id: str) -> str:
    """Create unique key for session."""
    return f"{session_id}:{window_id}:{pane_id}"


def find_session_by_pid(state: dict, claude_pid: int) -> Optional[str]:
    """Find session key by Claude PID."""
    for key, session in state["sessions"].items():
        if session.get("claude_pid") == claude_pid:
            return key
    return None


@with_lock
def cmd_start(pid: int):
    """Register session, mark as idle (waiting for user input)."""
    log("SessionStart", f"start called with pid={pid}")
    state = load_state()

    location = find_pane_by_pid(pid)
    if not location:
        log("SessionStart", f"ERROR: Could not find pane for PID {pid}")
        print("Could not find pane for PID", file=sys.stderr)
        return

    session_id, window_id, pane_id = location
    new_key = make_key(session_id, window_id, pane_id)
    log("SessionStart", f"Found location: {new_key}")

    # Check if PID already exists with different location
    old_key = find_session_by_pid(state, pid)
    if old_key and old_key != new_key:
        log("SessionStart", f"Location changed from {old_key} to {new_key}")
        del state["sessions"][old_key]

    now = datetime.now().isoformat()
    if new_key not in state["sessions"]:
        state["sessions"][new_key] = {
            "session_id": session_id,
            "window_id": window_id,
            "pane_id": pane_id,
            "claude_pid": pid,
            "status": "idle",
            "last_prompt": get_last_prompt(pane_id),
            "started_at": now,
            "updated_at": now,
            "turns": 0,
        }

    save_state(state)
    log("SessionStart", f"Saved: {new_key}")


@with_lock
def cmd_running(pid: int):
    """Mark session as running (agent is working)."""
    # Read prompt from stdin (hook passes JSON via stdin)
    prompt = ""
    try:
        if not sys.stdin.isatty():
            data = json.load(sys.stdin)
            prompt = data.get("prompt", "")
            log("UserPromptSubmit", f"Got prompt from stdin: '{prompt[:50]}...'")
    except Exception as e:
        log("UserPromptSubmit", f"Failed to read stdin: {e}")

    log("UserPromptSubmit", f"running called with pid={pid}")
    state = load_state()
    key = find_session_by_pid(state, pid)
    if key:
        state["sessions"][key]["status"] = "running"
        state["sessions"][key]["updated_at"] = datetime.now().isoformat()
        state["sessions"][key]["turns"] = state["sessions"][key].get("turns", 0) + 1
        if prompt:
            state["sessions"][key]["last_prompt"] = prompt
        save_state(state)
        log("UserPromptSubmit", f"Marked {key} as running")
    else:
        log("UserPromptSubmit", f"WARNING: PID {pid} not found in state")


@with_lock
def cmd_completed(pid: int):
    """Mark session as completed (task done, waiting for user review)."""
    log("Stop", f"completed called with pid={pid}")
    state = load_state()
    key = find_session_by_pid(state, pid)
    if key:
        state["sessions"][key]["status"] = "completed"
        state["sessions"][key]["updated_at"] = datetime.now().isoformat()
        save_state(state)
        log("Stop", f"Marked {key} as completed")
    else:
        log("Stop", f"WARNING: PID {pid} not found in state")


@with_lock
def cmd_remove(pid: int):
    """Remove session record by PID."""
    log("SessionEnd", f"remove called with pid={pid}")
    state = load_state()
    key = find_session_by_pid(state, pid)
    if key:
        del state["sessions"][key]
        save_state(state)
        log("SessionEnd", f"Removed: {key}")
    else:
        log("SessionEnd", f"WARNING: PID {pid} not found in state")


@with_lock
def cmd_remove_pane(pane_id: str):
    """Remove session record for pane."""
    state = load_state()
    keys_to_remove = [
        k for k, s in state["sessions"].items()
        if s.get("pane_id") == pane_id
    ]
    for key in keys_to_remove:
        del state["sessions"][key]
    if keys_to_remove:
        save_state(state)


def cmd_status():
    """Output status bar content."""
    state = load_state()
    counts = {"running": 0, "completed": 0, "idle": 0}
    for session in state["sessions"].values():
        status = session.get("status", "idle")
        if status in counts:
            counts[status] += 1

    parts = []
    for status, count in counts.items():
        if count > 0:
            parts.append(f"{STATUS_ICONS.get(status, '?')}{count}")

    print(" ".join(parts) if parts else "")


@with_lock
def cmd_list():
    """List all sessions as JSON."""
    state = load_state()
    print(json.dumps(state["sessions"], indent=2, ensure_ascii=False))


@with_lock
def cmd_clear():
    """Clear all records."""
    save_state({"sessions": {}, "updated_at": ""})
    print("Cleared all records")


@with_lock
def cmd_clean():
    """Clean up stale records (panes or processes that no longer exist)."""
    state = load_state()

    # Get all existing panes
    output = run_tmux("list-panes", "-a", "-F", "#{pane_id}")
    existing_panes = set(output.split("\n")) if output else set()

    keys_to_remove = []
    for key, session in state["sessions"].items():
        pane_id = session.get("pane_id", "")
        claude_pid = session.get("claude_pid", 0)

        # Check if pane no longer exists
        if pane_id not in existing_panes:
            keys_to_remove.append(key)
            continue

        # Check if Claude process is dead
        if claude_pid:
            try:
                os.kill(claude_pid, 0)  # Check if process exists
            except (OSError, ProcessLookupError):
                keys_to_remove.append(key)

    for key in keys_to_remove:
        del state["sessions"][key]

    if keys_to_remove:
        save_state(state)
        print(f"Cleaned {len(keys_to_remove)} stale records")
    else:
        print("No stale records found")


def cmd_tui():
    """Launch TUI."""
    try:
        from textual.app import App
        from textual.widgets import Header, Footer, Static
        from textual.containers import Container
        from textual.reactive import reactive
    except ImportError:
        print("Error: textual not installed. Run: pip install textual", file=sys.stderr)
        sys.exit(1)

    class ClaudeWatcherApp(App):
        CSS = """
        Screen {
            layout: vertical;
        }
        .session-item {
            padding: 1 2;
        }
        .session-item.selected {
            background: $primary;
            color: $text;
        }
        .empty-message {
            padding: 1 2;
            text-align: center;
        }
        .status-icon {
            text-style: bold;
        }
        """

        def __init__(self):
            super().__init__()
            self.theme = "ansi-dark"

        BINDINGS = [
            ("u", "up", "Up"),
            ("e", "down", "Down"),
            ("up", "up", "Up"),
            ("down", "down", "Down"),
            ("enter", "focus_pane", "Focus"),
            ("r", "refresh", "Refresh"),
            ("c", "clean", "Clean"),
            ("q", "quit", "Quit"),
            ("escape", "quit", "Quit"),
        ]

        selected_index = reactive(0)
        sessions = reactive([])

        def compose(self):
            yield Header()
            yield Container(id="sessions")
            yield Footer()

        def get_title(self) -> str:
            """Generate title with status counts."""
            state = load_state()
            counts = {"running": 0, "completed": 0, "idle": 0}
            for session in state["sessions"].values():
                status = session.get("status", "")
                if status in counts:
                    counts[status] += 1

            parts = []
            if counts["running"] > 0:
                parts.append(f"{counts['running']} running")
            if counts["completed"] > 0:
                parts.append(f"{counts['completed']} completed")
            if counts["idle"] > 0:
                parts.append(f"{counts['idle']} idle")

            return "Claude Watcher" + (" · " + " · ".join(parts) if parts else "")

        def on_mount(self):
            self.title = self.get_title()
            self.refresh_sessions()
            self.set_interval(2, self.refresh_sessions)

        def refresh_sessions(self):
            self.title = self.get_title()
            state = load_state()
            # Sort by updated_at, most recent first
            self.sessions = sorted(
                state["sessions"].items(),
                key=lambda x: x[1].get("updated_at", ""),
                reverse=True,
            )

            container = self.query_one("#sessions")
            container.remove_children()

            # Show empty state if no sessions
            if not self.sessions:
                container.mount(Static("当前 tmux 中没有 agent 会话", classes="empty-message"))
                return

            for i, (key, session) in enumerate(self.sessions):
                sid = session.get("session_id", "").lstrip("$")
                wid = session.get("window_id", "").lstrip("@")
                pane_id = session.get("pane_id", "").lstrip("%")

                # Get names by looking up pane_id in list-panes output
                raw_pane_id = session.get("pane_id", "")
                pane_list = run_tmux("list-panes", "-a", "-F", "#{pane_id} #{session_name} #{pane_current_command} #{pane_current_path}")
                session_name, pane_name, cwd = "?", "?", ""
                for line in pane_list.split("\n"):
                    parts = line.strip().split(maxsplit=3)
                    if len(parts) >= 3 and parts[0] == raw_pane_id:
                        session_name, pane_name = parts[1], parts[2]
                        cwd = parts[3] if len(parts) == 4 else ""
                        break

                if cwd:
                    # Shorten path: show last 2 directories
                    cwd_parts = cwd.split("/")
                    if len(cwd_parts) > 2:
                        cwd = "/".join(cwd_parts[-2:])
                    cwd = f"📁 {cwd}"

                status = session.get("status", "idle")
                icon = STATUS_ICONS.get(status, "?")
                # Use stored prompt (from hook), fallback to pane parsing
                summary = session.get("last_prompt", "") or get_last_prompt(raw_pane_id)
                turns = session.get("turns", 0)

                # Calculate time info
                updated = session.get("updated_at", "")
                started = session.get("started_at", "")
                time_info = ""
                try:
                    if status == "running" and started:
                        # Show running duration
                        start_dt = datetime.fromisoformat(started)
                        delta = datetime.now() - start_dt
                        secs = int(delta.total_seconds())
                        if secs < 60:
                            time_info = f"running {secs}s"
                        elif secs < 3600:
                            time_info = f"running {secs // 60}m {secs % 60}s"
                        else:
                            time_info = f"running {secs // 3600}h"
                    elif updated:
                        # Show inactive time (time since last update)
                        dt = datetime.fromisoformat(updated)
                        delta = datetime.now() - dt
                        secs = int(delta.total_seconds())
                        if secs < 60:
                            time_info = f"inactive {secs}s"
                        elif secs < 3600:
                            time_info = f"inactive {secs // 60}m"
                        else:
                            time_info = f"inactive {secs // 3600}h"
                except ValueError:
                    pass

                # Truncate summary to ~40 chars (half of typical terminal width)
                max_len = 40
                if len(summary) > max_len:
                    summary = summary[:max_len] + "..."

                css_class = "session-item selected" if i == self.selected_index else "session-item"
                text = f'{icon} {sid}:{wid}:{pane_id}({pane_name})    {cwd}\n   💬 "{summary}"\n   {time_info} · {turns} turns'

                container.mount(Static(text, classes=css_class))

        def action_up(self):
            if self.selected_index > 0:
                self.selected_index -= 1
                self.refresh_sessions()

        def action_down(self):
            if self.selected_index < len(self.sessions) - 1:
                self.selected_index += 1
                self.refresh_sessions()

        def action_focus_pane(self):
            if 0 <= self.selected_index < len(self.sessions):
                _, session = self.sessions[self.selected_index]
                pane_id = session.get("pane_id", "")
                window_id = session.get("window_id", "")
                if pane_id and window_id:
                    # Exit TUI first
                    self.exit()
                    # Select window then pane after popup closes
                    subprocess.run(["tmux", "run-shell", "-b", f"tmux select-window -t {window_id} && tmux select-pane -t {pane_id}"])

        def action_clean(self):
            cmd_clean()
            self.refresh_sessions()

        def action_refresh(self):
            self.refresh_sessions()

    app = ClaudeWatcherApp()
    app.run()


def main():
    parser = argparse.ArgumentParser(description="Claude Watcher")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # start command
    p_start = subparsers.add_parser("start", help="Register session (idle)")
    p_start.add_argument("--pid", type=int, required=True, help="Claude process PID")

    # running command
    p_running = subparsers.add_parser("running", help="Mark as running")
    p_running.add_argument("--pid", type=int, required=True, help="Claude process PID")

    # completed command
    p_completed = subparsers.add_parser("completed", help="Mark as completed")
    p_completed.add_argument("--pid", type=int, required=True, help="Claude process PID")

    # remove-pane command
    p_remove = subparsers.add_parser("remove-pane", help="Remove pane record")
    p_remove.add_argument("pane_id", help="Pane ID to remove")

    # remove command
    p_remove_pid = subparsers.add_parser("remove", help="Remove record by PID")
    p_remove_pid.add_argument("--pid", type=int, required=True, help="Claude process PID")

    # Other commands
    subparsers.add_parser("status", help="Output status bar content")
    subparsers.add_parser("list", help="List all sessions")
    subparsers.add_parser("clear", help="Clear all records")
    subparsers.add_parser("clean", help="Clean stale records")
    subparsers.add_parser("tui", help="Launch TUI")

    args = parser.parse_args()

    if args.command == "start":
        cmd_start(args.pid)
    elif args.command == "running":
        cmd_running(args.pid)
    elif args.command == "completed":
        cmd_completed(args.pid)
    elif args.command == "remove":
        cmd_remove(args.pid)
    elif args.command == "remove-pane":
        cmd_remove_pane(args.pane_id)
    elif args.command == "status":
        cmd_status()
    elif args.command == "list":
        cmd_list()
    elif args.command == "clear":
        cmd_clear()
    elif args.command == "clean":
        cmd_clean()
    elif args.command == "tui":
        cmd_tui()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
