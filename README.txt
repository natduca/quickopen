Open files in Vim or Emacs quickly with fuzzy expressions and a live-updating
UI, even for directory-trees containing hundreds of thousands of files.

Fuzzy? When you enter "rwh", quickopen finds files like
       RenderWidgetHost
       render-widget-host
       threaded_window_handler

The results are ranked by relevance. In 10s of milliseconds. So you get new results
as you type. Thus, you might refine 'rwh' to 'rwhcpp' to get
render_widget_host.cpp

Key features:
- Blazingly fast! 15ms search time on full 180k-file Chrome directory tree.
- Integration with vim gf and emacs ff-find-other-file when they get stuck
- Index maintained in-memory, persists across editor sessions/instances
- Reasonablly pretty GUI, with fallback to curses in terminal sessions
- Same backend shared between emacs and vim

Coming soon:
- Searches influenced by open/current buffers


Dependencies
================================================================================
Linux:
        python-gtk2

OSX:
        http://www.wxpython.org/download.php#stable
        wxPython 2.8-osx-unicode-2.6

Setting up the quickopen daemon
================================================================================
 0. Tell quickopen to index some directories...
      nduca: ~/quickopen $ ./quickopen add ~/chromium
      nduca: ~/quickopen $ ./quickopen add ~/quickopen
      nduca: ~/quickopen $ ./quickopen ignore \*LayoutTests\*

 1. Check quickopen's status:
      nduca: ~/quickopen $ ./quickopen rawsearch foo
      Database is not fully indexed. Wait a bit or try quickopen status

      nduca: ~/quickopen $ ./quickopen status
      Syncing: 17802 files found, 116 dirs pending

      nduca: ~/quickopen $ ./quickopen status
      up-to-date: 158553 files indexed; 2-threaded searches

VIM Setup
================================================================================

Using pathogen:
1. http://github.com/tpope/vim-pathogen
2. git submodule add https://github.com/natduca/quickopen ~/.vim/bundle/quickopen

By hand:
1. source quickopen/plugin/quickopen.vim

Emacs Setup
================================================================================

By hand:
  (load quickopen/elisp/quickopen.el)

Using site-lisp:
  git clone https://github.com/natduca/quickopen.git ~/.emacs/site-lisp

And if site-lisp isn't set up yet:
  (let ((site-lisp-dir (expand-file-name "~/.emacs/site-lisp")))
    (when (file-exists-p site-lisp-dir)
      (let ((default-directory site-lisp-dir))
        (normal-top-level-add-to-load-path '("."))
        (normal-top-level-add-subdirs-to-load-path))))

Consider setting up binding ff-find-other-file to a hotkey if you haven't done
so already. Quickopen will be used if the basic ff-find-other-file produces no
results:
  (global-set-key (kbd "M-o") (lambda ()
                                (interactive "")
                                (ff-find-other-file)
                                ))
  (global-set-key (kbd "M-O") (lambda ()
                                (interactive "")
                                (ff-find-other-file t)
                                ))

Visual SlickEdit Setup
================================================================================

 1. Ensure that the directory containing quickopend is in your path.

 2. Load the quickopen macro module by clicking Macro > Load Module..., and
    selecting slickedit/QuickOpen.e.

 3. Now set up a key binding for quick open.
    a) Click, Tools > Options...
    b) Expand 'Keyboard and Mouse'
    c) Select 'Key Bindings'
    d) Type QuickOpen in the 'Search by command:' text box. If all geos well,
       this command will exist and be found.
    e) Then click the 'Add..' button and bind to whichever keys you please,
       but I strongly recommend ctrl+shift+o for consistency with vim.

Usage
================================================================================

  1. VIM:              C-O                   (ctrl-shift-o)  to open
                       gf   c-w                              to goto file

     Emacs:            M-S-o                 (meta-shift-o)  to open
                       C-Q                                   to open

     Visual SlickEdit: C-O                   (ctrl-shift-o)  to open

  2. Command line
      nduca: ~/quickopen $ ./quickopen
         <brings up a GUI for a picking a file,
          prints file picked to stdout once done>
