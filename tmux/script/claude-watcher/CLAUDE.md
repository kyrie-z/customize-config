# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## 项目概述

Claude Watcher 是一个在 tmux 中跟踪多个 Claude Code 会话状态的工具。

## 常用命令

```bash
# 运行 TUI 界面
python3 claude_watcher.py tui

# 列出所有会话（JSON 格式）
python3 claude_watcher.py list

# 输出状态栏内容（用于 tmux 状态栏）
python3 claude_watcher.py status

# 清理过期记录
python3 claude_watcher.py clean

# 清除所有记录
python3 claude_watcher.py clear

# 查看日志
tail -f /tmp/claude-watcher.log
```

## 架构

单一 Python 脚本 (`claude_watcher.py`)，通过 Claude Code hooks 接收事件：

| 命令 | Hook | 触发时机 | 效果 |
|------|------|----------|------|
| `start --pid $PPID` | SessionStart | Claude 启动 | 注册会话，状态为 idle |
| `running --pid $PPID` | UserPromptSubmit | 用户提交消息 | 状态改为 running，记录 prompt |
| `completed --pid $PPID` | Stop | Claude 完成响应 | 状态改为 completed |
| `remove --pid $PPID` | SessionEnd | 会话结束 | 删除记录 |

### 会话定位原理

通过 TTY 匹配定位 Claude 所在的 tmux pane：
1. 用 `ps -p <pid> -o tty=` 获取进程的 TTY
2. 遍历 tmux panes 的 `#{pane_tty}` 找到匹配

### 状态存储

- 文件：`/tmp/claude-watcher-state.json`
- 使用文件锁（`fcntl.flock`）保证并发安全
- 每个会话记录包含：session_id, window_id, pane_id, claude_pid, status, last_prompt, updated_at, turns

### 状态说明

| 状态 | 图标 | 说明 |
|------|------|------|
| idle | 💤 | 空闲，等待用户输入 |
| running | 🤖 | 正在执行任务 |
| completed | ✅ | 任务完成，等待用户确认 |

## TUI 界面

- 每 1 秒自动刷新
- 显示：会话位置、任务摘要、状态图标、空闲/运行时长、对话轮次
- 快捷键：u/e 或 ↑↓ 导航，Enter 跳转到 pane，r 刷新，c 清理，q 退出

## 依赖

- Python 3.8+
- textual (TUI 框架): `uv pip install textual`
- tmux 3.0+
