" Copyright 2011 Google Inc.
"
" Licensed under the Apache License, Version 2.0 (the "License");
" you may not use this file except in compliance with the License.
" You may obtain a copy of the License at
"
"      http://www.apache.org/licenses/LICENSE-2.0
"
" Unless required by applicable law or agreed to in writing, software
" distributed under the License is distributed on an "AS IS" BASIS,
" WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
" See the License for the specific language governing permissions and
" limitations under the License.

if exists("loaded_quickopen")
  finish
endif
let loaded_quickopen = 1

let s:QuickOpenFile = resolve(expand("<sfile>"))
let s:QuickOpenDir = strpart(s:QuickOpenFile, 0, strridx(s:QuickOpenFile,"/plugin"))
let s:QuickOpenApp = s:QuickOpenDir . "/quickopen"

function! s:RunQuickOpen(args)
    let res = system(s:QuickOpenApp . " " . a:args)
    if v:shell_error
      echohl ErrorMsg
      echo substitute(escape(res, "\""), "\n$", "", "g")
      echohl None
      return []
    endif
    return split(res, "\n", 0)
endfunction

function! s:QuickOpenPrompt(query)
  if has("gui_running")
    return s:RunQuickOpen("prelaunch search " . a:query)
  else
    let resultsfile = tempname()

    exe "new __quickopen__"
    setlocal buftype=nofile
    setlocal bufhidden=hide
    setlocal noswapfile
    setlocal buflisted

    exec("silent! !" . s:QuickOpenApp . " search --curses --results-file=" . resultsfile . " --current-file=" . expand("%:p") . " " . a:query)
    exe "bdel"

    exec(":redraw!")
    let b = filereadable(resultsfile)
    if b
        let files = readfile(resultsfile)
        let b = delete(resultsfile)
    else
        let files = []
    endif
    return files
  endif
endfunction

function! s:QuickOpenSingle(cmd, query)
  let res = s:RunQuickOpen("search --only-if-exact-match " . a:query)
  if empty(res) || res[0] == ""
    call QuickFind(a:cmd, a:query)
    return
  endif
  exec(a:cmd . " " . fnameescape(res[0]))
endfunction

function! QuickFind(cmd, query)
  let files_to_open = s:QuickOpenPrompt(a:query)
  for f in files_to_open
    exec(a:cmd . " " . fnameescape(f))
  endfor
endfunction

" Ugh, someone with a clue about Vim, help me, what're good key bindings?
noremap <silent> <C-O> <Esc>:call QuickFind(':find', "")<CR>

noremap <silent> <D-O> <Esc>:call QuickFind(':find', "")<CR>

nnoremap <silent> gf :call <sid>QuickOpenSingle(':find', expand('<cfile>'))<cr>
nnoremap <silent> <c-w>gf :call <sid>QuickOpenSingle(':sp', expand('<cfile>'))<cr>
