

tui new-layout full_me {-horizontal cmd 1 {src 1 status 1 asm 1} 1} 1
set tui border-kind ascii

# lf: 进入 tui 并使用 full_me 布局
define lf
    layout full_me
    focus cmd
end
