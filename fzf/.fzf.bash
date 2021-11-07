# Setup fzf
# ---------
if [[ ! "$PATH" == */home/zzl/.fzf/bin* ]]; then
  export PATH="${PATH:+${PATH}:}/home/zzl/.fzf/bin"
fi

# Auto-completion
# ---------------
[[ $- == *i* ]] && source "/home/zzl/.fzf/shell/completion.bash" 2> /dev/null

# Key bindings
# ------------
source "/home/zzl/.fzf/shell/key-bindings.bash"

# 需要安装bat
export FZF_DEFAULT_OPTS=' --layout=reverse --border --preview "bat --color=always --style=numbers --line-range=:500 {} "'
# 需要安装silversearcher-ag
export FZF_DEFAULT_COMMAND='ag --hidden --ignore .git --ignore node_modules --ignore-dir /media --ignore-dir /tmp  -l -g "" /' 
export FZF_COMPLETION_TRIGGER='\'


