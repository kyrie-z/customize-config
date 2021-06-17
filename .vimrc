	syntax enable   "语法高亮
	syntax on
set scrolloff=5 
filetype on " 侦测文件类型
set tabstop=4
set shiftwidth=4
set expandtab
set smarttab
set autoread
set nu
set nocursorline
set cindent
set autoindent
set smartindent
set clipboard=unnamed
set confirm
set backspace=2 " 使回格键（backspace）正常处理indent, eol, start等
"set whichwrap+=<,>,h,l    "允许跨行

"搜索逐字符高亮
set hlsearch
set incsearch

"禁止生成临时文件
set nobackup
set noswapfile

set showcmd             " Show partial command in status line.
set showmatch           " 括号匹配
set autowrite           " Automatically save before commands like :next and :make
set hidden              " Hide buffers when they are abandoned
set mouse=a             " Enable mouse usage (all modes)
set mouse=i
set paste
set noexpandtab
set scrolloff=5 "顶部和底部时保持n行距离


"分屏操
map sl :set splitright<CR>:vsplit<CR>
map sh :set nosplitright<CR>:vsplit<CR>
map sj :set splitbelow<CR>:split<CR>
map sk :set nosplitbelow<CR>:split<CR>
"切换Buffer快捷键
nnoremap <C-w>] :bn<CR> 
nnoremap <C-w>[ :bp<CR>
nnoremap <C-w>- :bd<CR>




"--------插件---------
call plug#begin('~/.vim/plugged')
Plug 'preservim/nerdtree'
Plug 'vim-airline/vim-airline'
Plug 'majutsushi/tagbar'
call plug#end()

"--------目录树
map tt :NERDTreeToggle<CR>

"--------导航栏
let g:airline#extensions#whitespace#enabled = 0  "取消whitespace显示

"打开tabline
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#buffer_nr_show = 1

"--------tagbar
let g:tagbar_width=35
let g:tagbar_autofocus=1
let g:tagbar_right = 1
nmap <F3> :TagbarToggle<CR>
