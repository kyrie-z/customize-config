syntax on
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
set backspace=2 

map sl :set splitright<CR>:vsplit<CR>
map sh :set nosplitright<CR>:vsplit<CR>
map sj :set splitbelow<CR>:split<CR>
map sk :set nosplitbelow<CR>:split<CR>

set showcmd		" Show partial command in status line.
set showmatch		" Show matching brackets.
"set ignorecase		" Do case insensitive matching
"set smartcase		" Do smart case matching
set incsearch		" Incremental search
set autowrite		" Automatically save before commands like :next and :make
set hidden		" Hide buffers when they are abandoned
set mouse=a		" Enable mouse usage (all modes)
set mouse=i
set paste
set noexpandtab
" Source a global configuration file if available

set scrolloff=5 


call plug#begin('~/.vim/plugged')
Plug 'ycm-core/YouCompleteMe'
Plug 'preservim/nerdtree'
Plug 'vim-airline/vim-airline'
Plug 'fatih/vim-go', { 'do': ':GoUpdateBinaries' }
call plug#end()

map tt :NERDTreeToggle<CR>

nnoremap gd :YcmCompleter GoToDefinitionElseDeclaration<CR>
