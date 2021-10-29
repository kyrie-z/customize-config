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
"set paste              " Don't use it , Cause auto-completion not work
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


"--------插件---------
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
  let g:floaterm_keymap_new    = '<C-c>'
  let g:floaterm_keymap_toggle = '<C-h>'
  let g:floaterm_keymap_kill   = '<C-k>'

"============coc.nvim==============
let g:coc_disable_startup_warning = 1

let g:coc_global_extensions = ['coc-json', 'coc-vimlsp', 'coc-highlight', 'coc-marketplace', 'coc-go', 'coc-clangd']

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


" Use `[g` and `]g` to navigate diagnostics
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
autocmd CursorHold * silent call CocActionAsync('highlight')





