#!/usr/bin/env python3
"""
Claude Watcher - 在 tmux 中跟踪多个 Claude Code 会话的状态

这个工具通过 Claude Code 的 hooks 系统（SessionStart/UserPromptSubmit/Stop/SessionEnd）
来追踪每个会话的运行状态（idle/running/completed），并在 TUI 中显示。

状态存储: /tmp/claude-watcher-state.json
日志文件: /tmp/claude-watcher.log
"""

import argparse
import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 文件路径常量
STATE_FILE = Path("/tmp/claude-watcher-state.json")  # 存储所有会话状态的 JSON 文件
LOCK_FILE = Path("/tmp/claude-watcher-state.lock")   # 文件锁，防止并发写入冲突
LOG_FILE = Path("/tmp/claude-watcher.log")           # 调试日志文件

# 状态对应的显示图标
STATUS_ICONS = {
    "running": "🤖",    # 正在执行任务
    "completed": "✅",  # 任务完成，等待用户确认
    "idle": "💤",       # 空闲，等待用户输入
}


def log(hook_name: str, message: str):
    """
    写入日志到文件，用于调试。

    Args:
        hook_name: hook 名称（如 SessionStart, UserPromptSubmit）
        message: 日志消息内容
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} [{hook_name}] {message}\n")


def run_tmux(*args: str) -> str:
    """
    执行 tmux 命令并返回输出。

    Args:
        *args: tmux 命令参数，如 "list-panes", "-a"

    Returns:
        tmux 命令的标准输出，失败返回空字符串
    """
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


def get_pid_tty(pid: int) -> Optional[str]:
    """
    获取进程对应的 TTY 设备路径。

    Args:
        pid: 进程 PID

    Returns:
        TTY 路径（如 "/dev/pts/1"），失败返回 None
    """
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "tty=", "--no-headers"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        tty_name = result.stdout.strip()
        if tty_name and tty_name != "?":
            return f"/dev/{tty_name}"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def find_pane_by_pid(claude_pid: int) -> Optional[tuple[str, str, str]]:
    """
    根据 Claude 进程的 PID 找到它所在的 tmux pane。

    通过比对进程的 TTY 和 pane 的 TTY 来定位。

    Args:
        claude_pid: Claude 进程的 PID

    Returns:
        (session_id, window_id, pane_id) 元组，找不到返回 None
    """
    # 获取 Claude 进程的 TTY
    claude_tty = get_pid_tty(claude_pid)
    if not claude_tty:
        return None

    # 获取所有 tmux panes 的 TTY 映射
    output = run_tmux("list-panes", "-a", "-F", "#{session_id} #{window_id} #{pane_id} #{pane_tty}")
    if not output:
        return None

    # 找到 TTY 匹配的 pane
    for line in output.split("\n"):
        parts = line.strip().split()
        if len(parts) != 4:
            continue
        session_id, window_id, pane_id, pane_tty = parts
        if pane_tty == claude_tty:
            return (session_id, window_id, pane_id)

    return None


def with_lock(func):
    """
    装饰器：在执行函数前获取文件锁，防止并发写入状态文件。

    用法：@with_lock
    """
    def wrapper(*args, **kwargs):
        with open(LOCK_FILE, "w") as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)  # 获取排他锁
            try:
                return func(*args, **kwargs)
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)  # 释放锁
    return wrapper


def load_state() -> dict:
    """
    从 JSON 文件加载会话状态。

    Returns:
        状态字典，格式为 {"sessions": {key: session_info}, "updated_at": "..."}
    """
    if not STATE_FILE.exists():
        return {"sessions": {}, "updated_at": ""}
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return {"sessions": {}, "updated_at": ""}


def save_state(state: dict):
    """
    保存状态到 JSON 文件。

    Args:
        state: 要保存的状态字典
    """
    state["updated_at"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def make_key(session_id: str, window_id: str, pane_id: str) -> str:
    """
    生成会话的唯一标识键。

    Returns:
        格式如 "session_name:window_id:pane_id"
    """
    return f"{session_id}:{window_id}:{pane_id}"


def find_session_by_pid(state: dict, claude_pid: int) -> Optional[str]:
    """
    根据 Claude PID 在状态中查找对应的会话键。

    Returns:
        会话键，找不到返回 None
    """
    for key, session in state["sessions"].items():
        if session.get("claude_pid") == claude_pid:
            return key
    return None



@with_lock
def cmd_start(pid: int):
    """
    [Hook: SessionStart] 注册新会话，初始状态设为 idle。

    这个命令在 Claude Code 启动时被调用。

    Args:
        pid: Claude 进程的 PID
    """
    log("SessionStart", f"start called with pid={pid}")
    state = load_state()

    # 根据 PID 找到对应的 tmux pane
    location = find_pane_by_pid(pid)
    if not location:
        log("SessionStart", f"ERROR: Could not find pane for PID {pid}")
        print("Could not find pane for PID", file=sys.stderr)
        return

    session_id, window_id, pane_id = location
    new_key = make_key(session_id, window_id, pane_id)
    log("SessionStart", f"Found location: {new_key}")

    # 如果该 PID 已存在但位置变了，删除旧记录
    old_key = find_session_by_pid(state, pid)
    if old_key and old_key != new_key:
        log("SessionStart", f"Location changed from {old_key} to {new_key}")
        del state["sessions"][old_key]

    # 创建新会话记录
    now = datetime.now().isoformat()
    if new_key not in state["sessions"]:
        state["sessions"][new_key] = {
            "session_id": session_id,
            "window_id": window_id,
            "pane_id": pane_id,
            "claude_pid": pid,
            "status": "idle",           # 初始状态为空闲
            "last_prompt": "",          # 初始为空，等待用户输入
            "updated_at": now,
            "turns": 0,                 # 对话轮次计数
        }

    save_state(state)
    log("SessionStart", f"Saved: {new_key}")


@with_lock
def cmd_running(pid: int):
    """
    [Hook: UserPromptSubmit] 标记会话为 running（Claude 正在工作）。

    这个命令在用户提交消息后被调用。Hook 会通过 stdin 传入 JSON 数据。

    Args:
        pid: Claude 进程的 PID
    """
    # 从 stdin 读取 hook 传入的 JSON 数据（包含用户输入的 prompt）
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
    """
    [Hook: Stop] 标记会话为 completed（任务完成，等待用户确认）。

    这个命令在 Claude 完成一个任务后被调用。

    Args:
        pid: Claude 进程的 PID
    """
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
    """
    [Hook: SessionEnd] 删除会话记录。

    这个命令在 Claude Code 会话结束时被调用。

    Args:
        pid: Claude 进程的 PID
    """
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
    """
    根据 pane ID 删除会话记录。

    Args:
        pane_id: tmux pane ID（如 %0）
    """
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
    """
    输出状态栏内容，格式如 "🤖2 ✅1 💤3"。

    用于在 tmux 状态栏中显示。
    """
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
    """以 JSON 格式输出所有会话信息。"""
    state = load_state()
    print(json.dumps(state["sessions"], indent=2, ensure_ascii=False))


@with_lock
def cmd_clear():
    """清空所有会话记录。"""
    save_state({"sessions": {}, "updated_at": ""})
    print("Cleared all records")


@with_lock
def cmd_clean():
    """
    清理过期的会话记录。

    删除以下情况的记录：
    1. pane 已经不存在
    2. Claude 进程已经终止
    """
    state = load_state()

    # 获取所有存在的 panes
    output = run_tmux("list-panes", "-a", "-F", "#{pane_id}")
    existing_panes = set(output.split("\n")) if output else set()

    keys_to_remove = []
    for key, session in state["sessions"].items():
        pane_id = session.get("pane_id", "")
        claude_pid = session.get("claude_pid", 0)

        # 检查 pane 是否还存在
        if pane_id not in existing_panes:
            keys_to_remove.append(key)
            continue

        # 检查 Claude 进程是否还活着
        if claude_pid:
            try:
                os.kill(claude_pid, 0)  # 发送信号 0 不会真的杀死进程，只是检查是否存在
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
    """
    启动 TUI（终端用户界面）。

    使用 textual 库构建交互式界面，显示所有会话状态。
    支持键盘导航、跳转到对应 pane 等操作。
    """
    try:
        from textual.app import App
        from textual.widgets import Header, Footer, Static
        from textual.containers import Container
        from textual.reactive import reactive
    except ImportError:
        print("Error: textual not installed. Run: pip install textual", file=sys.stderr)
        sys.exit(1)

    class ClaudeWatcherApp(App):
        """
        Claude Watcher 的 TUI 应用类。

        显示所有会话列表，支持：
        - 上/下键或 u/e 键导航
        - Enter 键跳转到对应 tmux pane
        - r 键刷新
        - c 键清理过期记录
        - q/Esc 键退出
        """
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

        # 键盘快捷键绑定
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

        # 响应式变量：选中索引和会话列表
        selected_index = reactive(0)
        sessions = reactive([])

        def compose(self):
            """构建界面布局：Header + 会话列表容器 + Footer"""
            yield Header()
            yield Container(id="sessions")
            yield Footer()

        def get_title(self) -> str:
            """生成标题，包含各状态的数量统计。"""
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
            """界面启动时初始化：设置标题、刷新列表、启动定时刷新。"""
            self.title = self.get_title()
            self.refresh_sessions()
            self.set_interval(1, self.refresh_sessions)  # 每 1 秒刷新一次

        def refresh_sessions(self):
            """刷新会话列表显示。"""
            self.title = self.get_title()
            state = load_state()
            # 按更新时间倒序排列
            self.sessions = sorted(
                state["sessions"].items(),
                key=lambda x: x[1].get("updated_at", ""),
                reverse=True,
            )

            container = self.query_one("#sessions")
            container.remove_children()

            # 无会话时显示提示
            if not self.sessions:
                container.mount(Static("当前 tmux 中没有 agent 会话", classes="empty-message"))
                return

            # 渲染每个会话
            for i, (key, session) in enumerate(self.sessions):
                sid = session.get("session_id", "").lstrip("$")
                wid = session.get("window_id", "").lstrip("@")
                pane_id = session.get("pane_id", "").lstrip("%")

                # 从 tmux 获取 session 名称、当前命令、当前路径
                raw_pane_id = session.get("pane_id", "")
                pane_list = run_tmux("list-panes", "-a", "-F", "#{pane_id} #{session_name} #{pane_current_command} #{pane_current_path}")
                session_name, pane_name, cwd = "?", "?", ""
                for line in pane_list.split("\n"):
                    parts = line.strip().split(maxsplit=3)
                    if len(parts) >= 3 and parts[0] == raw_pane_id:
                        session_name, pane_name = parts[1], parts[2]
                        cwd = parts[3] if len(parts) == 4 else ""
                        break

                # 缩短路径显示
                if cwd:
                    cwd_parts = cwd.split("/")
                    if len(cwd_parts) > 2:
                        cwd = "/".join(cwd_parts[-2:])
                    cwd = f"📁 {cwd}"

                status = session.get("status", "idle")
                icon = STATUS_ICONS.get(status, "?")
                summary = session.get("last_prompt", "")
                turns = session.get("turns", 0)

                # 计算时间信息（距离上次更新的时长）
                updated = session.get("updated_at", "")
                time_info = ""
                if updated:
                    try:
                        dt = datetime.fromisoformat(updated)
                        delta = datetime.now() - dt
                        secs = int(delta.total_seconds())
                        if status == "running":
                            # 运行中：显示已运行时长
                            if secs < 60:
                                time_info = f"running {secs}s"
                            elif secs < 3600:
                                time_info = f"running {secs // 60}m {secs % 60}s"
                            else:
                                time_info = f"running {secs // 3600}h"
                        else:
                            # 空闲/完成：显示距离上次活动时长
                            if secs < 60:
                                time_info = f"inactive {secs}s"
                            elif secs < 3600:
                                time_info = f"inactive {secs // 60}m"
                            else:
                                time_info = f"inactive {secs // 3600}h"
                    except ValueError:
                        pass

                # 截断摘要
                max_len = 40
                if len(summary) > max_len:
                    summary = summary[:max_len] + "..."

                css_class = "session-item selected" if i == self.selected_index else "session-item"
                text = f'{icon} {sid}:{wid}:{pane_id}({pane_name})    {cwd}\n   💬 "{summary}"\n   {time_info} · {turns} turns'

                container.mount(Static(text, classes=css_class))

        def action_up(self):
            """向上移动选中。"""
            if self.selected_index > 0:
                self.selected_index -= 1
                self.refresh_sessions()

        def action_down(self):
            """向下移动选中。"""
            if self.selected_index < len(self.sessions) - 1:
                self.selected_index += 1
                self.refresh_sessions()

        def action_focus_pane(self):
            """跳转到选中的 tmux pane。"""
            if 0 <= self.selected_index < len(self.sessions):
                _, session = self.sessions[self.selected_index]
                pane_id = session.get("pane_id", "")
                window_id = session.get("window_id", "")
                if pane_id and window_id:
                    self.exit()
                    # 先选窗口再选 pane
                    subprocess.run(["tmux", "run-shell", "-b", f"tmux select-window -t {window_id} && tmux select-pane -t {pane_id}"])

        def action_clean(self):
            """清理过期记录并刷新。"""
            cmd_clean()
            self.refresh_sessions()

        def action_refresh(self):
            """手动刷新。"""
            self.refresh_sessions()

    app = ClaudeWatcherApp()
    app.run()


def main():
    """命令行入口：解析参数并调用对应命令。"""
    parser = argparse.ArgumentParser(description="Claude Watcher")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # ========== 定义命令行参数 ==========

    # Hook 命令（由 Claude Code hooks 调用）
    subparsers.add_parser("start", help="Register session (idle)").add_argument("--pid", type=int, required=True)
    subparsers.add_parser("running", help="Mark as running").add_argument("--pid", type=int, required=True)
    subparsers.add_parser("completed", help="Mark as completed").add_argument("--pid", type=int, required=True)
    subparsers.add_parser("remove", help="Remove record by PID").add_argument("--pid", type=int, required=True)
    subparsers.add_parser("remove-pane", help="Remove pane record").add_argument("pane_id")

    # 用户命令
    subparsers.add_parser("status", help="Output status bar content")
    subparsers.add_parser("list", help="List all sessions")
    subparsers.add_parser("clear", help="Clear all records")
    subparsers.add_parser("clean", help="Clean stale records")
    subparsers.add_parser("tui", help="Launch TUI")

    # ========== 解析并执行 ==========

    args = parser.parse_args()

    # 命令到函数的映射
    commands = {
        "start": lambda: cmd_start(args.pid),
        "running": lambda: cmd_running(args.pid),
        "completed": lambda: cmd_completed(args.pid),
        "remove": lambda: cmd_remove(args.pid),
        "remove-pane": lambda: cmd_remove_pane(args.pane_id),
        "status": cmd_status,
        "list": cmd_list,
        "clear": cmd_clear,
        "clean": cmd_clean,
        "tui": cmd_tui,
    }

    if args.command in commands:
        commands[args.command]()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
