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

function! s:GetDefaultBasePath()
  let cwd = getcwd()

  let dirs = split(cwd, "/")
  for ix in range(len(dirs) - 1, 0, -1)
    let dir = "/" . join(dirs[0:ix], "/") . "/"
    if isdirectory(dir . ".git")
      return dir
    endif
  endfor
  return ""
endfunction

function! s:RunQuickOpen(args)
  let res = system(s:QuickOpenApp . " " . a:args)
  let source_path = s:GetDefaultBasePath()
  let base_path_arg = ""
  if source_path != ""
    let base_path_arg = " --base-path=" . source_path
  endif

  let res = system(s:QuickOpenApp . " " . a:args . " --current-file=" . expand("%:p") . base_path_arg)
  if v:shell_error
    echohl ErrorMsg
    echo substitute(escape(res, "\""), "\n$", "", "g")
    echohl None
    return []
  endif
  return split(res, "\n", 0)
endfunction

let s:TermCallback = {}
function! s:TermCallback.on_exit(id, code, event)
  exe "bdel!"
  call s:OpenFiles(self.cmd, s:ReadResults(self.resultsfile))
endfunction

function! s:ReadResults(resultsfile)
  let b = filereadable(a:resultsfile)
  if b
    let files = readfile(a:resultsfile)
    let b = delete(a:resultsfile)
  else
    let files = []
  endif
  return files
endfunction

function! s:QuickOpenPrompt(cmd, query)
  if has("gui_running")
    return s:RunQuickOpen("prelaunch search " . a:query)
  endif

  let resultsfile = tempname()

  if !has("nvim")
    exe "new __quickopen__"
  else
    exe "e __quickopen__"
  endif

  setlocal buftype=nofile
  setlocal bufhidden=hide
  setlocal noswapfile
  setlocal buflisted
  let source_path = s:GetDefaultBasePath()
  let base_path_arg = ""
  if source_path != ""
    let base_path_arg = " --base-path=" . source_path
  endif

  let quickOpenCmd = s:QuickOpenApp . " search --curses --results-file=" . resultsfile . " --current-file=" . expand("%:p") . base_path_arg . " " . a:query
  if !has("nvim")
    exec("silent! !" . l:quickOpenCmd)
    exe "bdel"
    exec(":redraw!")
    return s:ReadResults(resultsfile)
  endif

  setlocal statusline=quickopen
  setlocal nonumber
  let s:TermCallback.resultsfile = l:resultsfile
  let s:TermCallback.cmd = a:cmd
  call termopen(l:quickOpenCmd, s:TermCallback)
  startinsert
  return []
endfunction

function! s:QuickOpenSingle(cmd, query)
  let res = s:RunQuickOpen("search --only-if-exact-match " . a:query)
  if empty(res) || res[0] == ""
    call QuickFind(a:cmd, a:query)
    return
  endif
  exec(a:cmd . " " . fnameescape(res[0]))
endfunction

function! s:OpenFiles(cmd, files_to_open)
  for f in a:files_to_open
    exec(a:cmd . " " . fnameescape(f))
  endfor
endfunction

function! QuickFind(cmd, query)
  let files_to_open = s:QuickOpenPrompt(a:cmd, a:query)
  call s:OpenFiles(a:cmd, l:files_to_open)
endfunction

com! -nargs=* O call QuickFind(":find", <q-args>)

nnoremap <silent> gf :call <sid>QuickOpenSingle(':find', expand('<cfile>'))<cr>
nnoremap <silent> <c-w>gf :call <sid>QuickOpenSingle(':sp', expand('<cfile>'))<cr>
