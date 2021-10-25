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
set relativenumber "relative position
set cursorline "highlight current line
set cindent
set autoindent
set smartindent
set clipboard=unnamed
set confirm
set backspace=2 " 使回格键（backspace）正常处理indent, eol, start等
"set whichwrap+=<,>,h,l    "允许跨行
set linebreak

set encoding=utf8
set guifont=DroidSansMono_Nerd_Font:h11
set wildmenu "cmd suggest

"搜索逐字符高亮
set hlsearch
set incsearch
set ignorecase
"ESC退出高亮
nnoremap <esc> :noh<CR> 
nnoremap <esc>^[ <esc>^[

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
"窗口调整
noremap = :vertical resize+5<CR>
noremap - :vertical resize-5<CR>
noremap . :res +5<CR>
noremap , :res -5<CR>
" Rotate screens
noremap srh <C-w>b<C-w>K
noremap srv <C-w>b<C-w>H


"切换Buffer快捷键
nnoremap <C-w>] :bn<CR> 
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

" coc.nvim setting
set updatetime=100
set shortmess+=c
inoremap <silent><expr> <TAB>
      \ pumvisible() ? "\<C-n>" :
      \ <SID>check_back_space() ? "\<TAB>" :
      \ coc#refresh()
inoremap <expr><S-TAB> pumvisible() ? "\<C-p>" : "\<C-h>"

function! s:check_back_space() abort
  let col = col('.') - 1
  return !col || getline('.')[col - 1]  =~# '\s'
endfunction

inoremap <silent><expr> <c-@> coc#refresh()
autocmd CursorHold * silent call CocActionAsync('highlight')


nmap ts <Plug>(coc-translator-p)

"--------插件---------
call plug#begin('~/.vim/plugged')
Plug 'preservim/nerdtree'
Plug 'vim-airline/vim-airline'
Plug 'majutsushi/tagbar'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'ryanoasis/vim-devicons'
Plug 'bling/vim-bufferline'
Plug 'tiagofumo/vim-nerdtree-syntax-highlight'

call plug#end()

"--------目录树
map tt :NERDTreeToggle<CR>

"--------导航栏
let g:airline#extensions#whitespace#enabled = 0  "取消whitespace显示

"--------tagbar
let g:tagbar_width=35
let g:tagbar_autofocus=1
let g:tagbar_right = 1
nmap <F3> :TagbarToggle<CR>

"============coc.nvim
let g:coc_disable_startup_warning = 1

let g:coc_global_extensions = ['coc-json', 'coc-vimlsp', 'coc-marketplace']

