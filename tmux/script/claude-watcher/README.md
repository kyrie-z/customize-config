# Claude Watcher

在 tmux 中跟踪多个 Claude Code 会话状态的工具。

## 功能

- 自动追踪所有 tmux 中的 Claude Code 会话
- 实时显示会话状态：运行中、空闲
- 显示工作目录和最近用户输入
- 快速跳转到对应 Claude 会话
- TUI 界面管理

## 状态图标

| 图标 | 状态 | 说明 |
|------|------|------|
| 🤖 | running | Claude 正在工作 |
| ✅ | completed | 任务完成，等待审核 |
| 💤 | idle | 空闲，等待用户输入 |

## 安装

### 1. 安装依赖

```bash
# 安装 textual (TUI 框架)
uv pip install textual --target ~/.local/lib/python3.13/site-packages
```

### 2. 创建软链接

```bash
ln -sf /path/to/claude-watcher/claude_watcher.py ~/.config/tmux/scripts/claude_watcher.py
```

### 3. 配置 Claude Code Hooks

在 `~/.claude/settings.json` 中添加：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.config/tmux/scripts/claude_watcher.py start --pid $PPID"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.config/tmux/scripts/claude_watcher.py running --pid $PPID"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.config/tmux/scripts/claude_watcher.py completed --pid $PPID"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.config/tmux/scripts/claude_watcher.py remove --pid $PPID"
          }
        ]
      }
    ]
  }
}
```

### 4. 配置 tmux

在 `~/.tmux.conf` 中添加：

```tmux
# prefix + a 打开 TUI
bind a display-popup -E -w 40% -h 40% -T "Claude Watcher" "python3 ~/.config/tmux/scripts/claude_watcher.py tui"

# pane 关闭时清理记录
set-hook -g pane-died 'run -b "python3 ~/.config/tmux/scripts/claude_watcher.py remove-pane #{pane_id}"'
```

## 使用

### TUI 界面

按 `prefix + a` 打开 TUI：

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Watcher · 1 running · 1 completed · 1 idle          │
├─────────────────────────────────────────────────────────────┤
│  🤖 0:claude                                                │
│     📁 tmux-config/.config                                  │
│     这里是最近的用户输入...                                  │
│     running 30s · 5 turns                                   │
│                                                             │
│  ✅ 1-project:claude                                        │
│     📁 home/zzl/project                                     │
│     确认是否继续？                                          │
│     2m ago · 3 turns                                        │
│                                                             │
│  💤 2-other:claude                                          │
│     📁 home/zzl/other                                       │
│     等待用户输入...                                         │
│     5m ago · 0 turns                                        │
├─────────────────────────────────────────────────────────────┤
│  [u/e] Navigate  [Enter] Focus  [r] Refresh  [c] Clean  [q] Quit │
└─────────────────────────────────────────────────────────────┘
```

### 快捷键

| 键 | 功能 |
|------|------|
| `u` / `↑` | 上移 |
| `e` / `↓` | 下移 |
| `Enter` | 跳转到对应 pane |
| `r` | 刷新页面 |
| `c` | 清理过期记录 |
| `q` / `Esc` | 退出 |

### 命令行

```bash
# 列出所有会话
python3 ~/.config/tmux/scripts/claude_watcher.py list

# 输出状态栏内容
python3 ~/.config/tmux/scripts/claude_watcher.py status

# 清理过期记录
python3 ~/.config/tmux/scripts/claude_watcher.py clean

# 清除所有记录
python3 ~/.config/tmux/scripts/claude_watcher.py clear
```

## 文件

```
claude-watcher/
├── README.md           # 本文档
└── claude_watcher.py   # 主程序
```

## 调试

日志文件：`/tmp/claude-watcher.log`

```bash
# 查看日志
tail -f /tmp/claude-watcher.log
```

## Hooks 说明

| Hook | 触发时机 | 命令 | 效果 |
|------|----------|------|------|
| SessionStart | Claude 启动 | start | 记录会话，状态为 idle |
| UserPromptSubmit | 用户提交输入 | running | 状态改为 running |
| Stop | 完成本轮响应 | completed | 状态改为 completed |
| SessionEnd | 会话结束 | remove | 删除记录 |

## 依赖

- Python 3.8+
- textual (TUI 框架)
- tmux 3.0+

## TODO

- task_summary 显示不准确
- py 脚本待删减
