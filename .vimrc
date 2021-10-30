"================================================= vim set =========================

set scrolloff=5		" leave least line 
filetype on 		" 侦测文件类型
set autoindent 		" 自动缩进（保持上个缩进）
set tabstop=4 		" 缩进格数
set expandtab 		" auto convert tabs to spaces 
set autoread 		" 打开文件监视
set nu
set relativenumber 	" relative position 相对行号
set cursorline 		" highlight current line
set backspace=indent,eol,start  	" 使回格键（backspace）正常处理indent, eol, start等
"set whichwrap+=h,l " 允许跨行
"set linebreak 		" 不会在单词内部折行
set encoding=utf8 	" 编码，使汉语正常显示

"search
set hlsearch 		" 搜索字符高亮
set incsearch 		" 跳转到搜索字符
set ignorecase 		" 搜索时忽略大小写 

"禁止生成临时文件
set nobackup 		" no backfile
set noswapfile 		" no .swp file

set showcmd             " Show partial command in status line.
set showmatch           " 括号匹配
set autowrite           " Automatically save before commands like :next and :make
set hidden              " Hide buffers when they are abandoned
set mouse=a             " Enable mouse usage (all modes)
set mouse=i
"set paste              " Don't use it , Cause auto-completion not work



"=============================================== vim key map ===============

let mapleader = "\<space>"


"==  Insert Mode   ==


"==  Visual Mode   ==
vnoremap y "+y 			" 共享粘贴
vmap <C-a> <Home> 	" cursor move
vmap <C-e> <End>


"==  Command Mode  ==
set wildmenu 			" 补全以菜单形式显示
cnoremap <C-a> <Home> 	" cursor move
cnoremap <C-e> <End>


"==  Normal Mode   ==
nmap <C-a> ^
nmap <C-e> $

"ESC退出高亮
nnoremap <esc> :noh<CR> 
nnoremap <esc>^[ <esc>^[


"窗口buffer操作
map sl :set splitright<CR>:vsplit<CR> 	" 分屏操作
map sh :set nosplitright<CR>:vsplit<CR>
map sj :set splitbelow<CR>:split<CR>
map sk :set nosplitbelow<CR>:split<CR>

noremap = :vertical resize+5<CR> 		" 窗口大小调整
noremap - :vertical resize-5<CR>
noremap . :res +5<CR>
noremap , :res -5<CR>

noremap srh <C-w>b<C-w>K 				" 窗口旋转 
noremap srv <C-w>b<C-w>H

nnoremap <C-w>] :bn<CR> 				" 切换Buffer快捷键 
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





"================================================ vim theme =====================

syntax enable   "语法高亮
"autocmd vimenter * hi Normal guibg=NONE ctermbg=NONE " transparent bg
set t_Co=256
set termguicolors
syntax on
let g:oceanic_next_terminal_bold = 1
let g:oceanic_next_terminal_italic = 1
colorscheme OceanicNext



"================================================ code set ===============

"==  Folding ==
set foldmethod=indent "用缩进表示折叠
set foldlevelstart=99 "打开文件是默认不折叠代码
"noremap <silent> <LEADER><LEADER> za
nnoremap <space> @=((foldclosed(line('.')) < 0) ? 'zc' : 'zo')<CR>

set cindent 	"c/c++自动缩进

map <silent> ;c :s/^/\/\//<CR>:noh<CR>      " 快速注释 
map <silent> ;u :s/\/\///<CR>:noh<CR>

"================================================= vim plugin =============


call plug#begin('~/.vim/plugged')
Plug 'preservim/nerdtree'
Plug 'itchyny/lightline.vim'
Plug 'majutsushi/tagbar'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'ryanoasis/vim-devicons'
Plug 'mengelbrecht/lightline-bufferline'
Plug 'tiagofumo/vim-nerdtree-syntax-highlight'
Plug 'voldikss/vim-floaterm'

call plug#end()


"--------目录树
map tt :NERDTreeToggle<CR>

"--------导航栏
set laststatus=2
set showtabline=2

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

"--------tagbar
let g:tagbar_width=35
let g:tagbar_autofocus=1
let g:tagbar_right = 1
nmap <F3> :TagbarToggle<CR>


"-------floaterm
  let g:floaterm_keymap_prev   = '<C-p>'
  let g:floaterm_keymap_next    = '<C-n>'
"  let g:floaterm_keymap_new    = '<C-c>'
  let g:floaterm_keymap_toggle = '<C-h>'
  let g:floaterm_keymap_kill   = '<C-k>'



"===============================================coc.nvim==============


let g:coc_global_extensions = ['coc-json', 'coc-vimlsp', 'coc-highlight', 'coc-marketplace', 'coc-go', 'coc-clangd']
let g:coc_disable_startup_warning = 1


let g:markdown_fenced_languages = [
      \ 'vim',
      \ 'help',
	  \ 'go',
	  \ 'c'
      \]

" coc.nvim setting
set cmdheight=2
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

" Make <CR> auto-select the first completion item and notify coc.nvim to
" format on enter, <cr> could be remapped by other vim plugin
inoremap <silent><expr> <cr> pumvisible() ? coc#_select_confirm()
                              \: "\<C-g>u\<CR>\<c-r>=coc#on_enter()\<CR>"


" Use `[e` and `]e` to navigate diagnostics
" Use `:CocDiagnostics` to get all diagnostics of current buffer in location list.
nmap <silent> [e <Plug>(coc-diagnostic-prev)
nmap <silent> ]e <Plug>(coc-diagnostic-next)

" GoTo code navigation.
nmap <silent> gd <Plug>(coc-definition)
nmap <silent> gy <Plug>(coc-type-definition)
nmap <silent> gi <Plug>(coc-implementation)
nmap <silent> gr <Plug>(coc-references)

" Use K to show documentation in preview window.
nnoremap <silent> K :call <SID>show_documentation()<CR>
function! s:show_documentation()
  if (index(['vim','help'], &filetype) >= 0)
    execute 'h '.expand('<cword>')
  elseif (coc#rpc#ready())
    call CocActionAsync('doHover')
  else
    execute '!' . &keywordprg . " " . expand('<cword>')
  endif
endfunction


" Highlight the symbol and its references when holding the cursor.
"autocmd CursorHold * silent call CocActionAsync('highlight')


