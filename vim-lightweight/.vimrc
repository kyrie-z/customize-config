" ============================== vim theme ==============================
syntax enable
set t_Co=256 

" set termguicolors
let g:oceanic_next_terminal_bold = 1
let g:oceanic_next_terminal_italic = 1
colorscheme OceanicNext


" ============================== vim set ==============================

set backspace=indent,eol,start          " 使回格键（backspace）正常处理indent, eol, start等
set wildmenu	    " 命令以菜单形式显示
set nobackup	    " 不创建交换文件
set noswapfile      " no .swp file
set autoread	    " 文件别其他程序修改时发出提示
set statusline+=%F  " 显示当前文件绝对路径
set mouse+=a
set nu
set showcmd	    " 底部显示正在输入的指令
set scrolloff=5	    " 留行
set cursorline	    " 行高亮显示
set ruler	    " 底部显示当前行列
set laststatus=2    " 显示状态栏
set showtabline=2

set hlsearch        " 搜索字符高亮
set incsearch       " 跳转到搜索字符
set ignorecase      " 搜索时忽略大小写
"ESC退出高亮
nnoremap <esc> :noh<CR>
nnoremap <esc>^[ <esc>^[

set softtabstop=4   " set tabstop=4    

set encoding=utf-8  

" 解决vim命令行显示未知符号
let &t_TI = ""
let &t_TE = ""

" ============================== vim key map ==============================

" install vim-athena
vnoremap y "+y	    " +y 复制到系统粘贴板上

nmap <C-a> <Home>
nmap <C-e> <End>
imap <C-a> <Home>
imap <C-e> <End>
vmap <C-a> <Home>
vmap <C-e> <End>


noremap = :vertical resize+5<CR>    " 窗口大小调整
noremap - :vertical resize-5<CR>
noremap + :res +5<CR>
noremap _ :res -5<CR>

nnoremap <C-w>] :bn<CR>             " 切换Buffer快捷键
nnoremap <C-w>[ :bp<CR>
nnoremap <C-w>- :bd<CR>
nmap <C-w>1 :b 1<CR>
nmap <C-w>2 :b 2<CR>
nmap <C-w>3 :b 3<CR>
nmap <C-w>4 :b 4<CR>
nmap <C-w>5 :b 5<CR>
nmap <C-w>6 :b 6<CR>
nmap <C-w>7 :b 7<CR>
nmap <C-w>8 :b 8<CR>
nmap <C-w>9 :b 9<CR>


" ============================== vim plugin ==============================

call plug#begin('~/.vim/plugged')
Plug 'majutsushi/tagbar'
Plug 'itchyny/vim-cursorword'
Plug 'itchyny/lightline.vim'
Plug 'mengelbrecht/lightline-bufferline'
call plug#end()

"---------- lightline

let g:lightline = {
      \ 'colorscheme': 'wombat',
      \ 'active': {
      \   'left': [ [ 'mode', 'paste' ], [ 'readonly', 'filename', 'modified' ] ]
      \ },
      \ 'tabline': {
      \   'left': [ ['buffers'] ],
      \   'right': [ ['close'] ]
      \ },
      \ 'component_expand': {
      \   'buffers': 'lightline#bufferline#buffers'
      \ },
      \ 'component_type': {
      \   'buffers': 'tabsel'
      \ }
      \ }

 let g:lightline#bufferline#enable_devicons = 1
 let g:lightline#bufferline#show_number = 3
let g:lightline#bufferline#number_map = {
\ 0: '₀', 1: '₁', 2: '₂', 3: '₃', 4: '₄',
\ 5: '₅', 6: '₆', 7: '₇', 8: '₈', 9: '₉'}


"---------- tagbar
let g:tagbar_width=35
let g:tagbar_autofocus=1
let g:tagbar_right = 1
nmap <F3> :TagbarToggle<CR>


"---------- vim-cursorword
 let g:cursorword_delay = 0  "禁止同单词移动闪烁


