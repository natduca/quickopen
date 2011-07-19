let s:QuickOpenFile=expand("<sfile>")

function! QuickOpenPrompt()
  let quickopen_dir = strpart(s:QuickOpenFile, 0, strridx(s:QuickOpenFile,'/'))
  let quickopen_app = quickopen_dir . '/quickopen'
  echo quickopen_app
  return system(quickopen_app)
endfunction

function! QuickFind()
  let file_to_open = QuickOpenPrompt()
  if file_to_open != ''
    exe ':find ' . file_to_open
  endif
endfunction

" Ugh, someone with a clue about Vim, help me, what're good key bindings?
noremap <silent> <C-O> <Esc>:call QuickFind()<CR>

noremap <silent> <D-O> <Esc>:call QuickFind()<CR>
