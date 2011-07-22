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

let s:QuickOpenFile=resolve(expand("<sfile>"))

function! QuickOpenPrompt()
  let quickopen_dir = strpart(s:QuickOpenFile, 0, strridx(s:QuickOpenFile,'/plugin'))
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
