`quickopen` lets you open files in Vim, Emacs and even SlickEdit quickly with fuzzy expressions, a live-updating
UI, even for directory-trees containing hundreds of thousands of files. Its UI works on Mac, Linux, Windows, and even a curses mode if you're stuck on VPN.

Fuzzy? When you enter "rwh", quickopen finds files like

- `RenderWidgetHost.cpp`
- `render-widget-host.h`
- `threaded_window_handler.h`

The results are ranked by relevance. In mere milliseconds. So you get new results
as you type. Thus, you might refine `rwh` to `rwhcpp` to get
`render_widget_host.cpp`

Key features:

- Blazingly fast! 15ms search time on full 360k-file Chrome directory tree.
- Integration with vim gf and emacs ff-find-other-file
- Index instantly searchable from any process, even command line
- Reasonablly pretty GUI, with fallback to curses in terminal sessions
- Same backend shared between emacs and vim, written in python


Dependencies
================================================================================
- Linux: python-gtk2
- OSX or Windows: chrome.

  Yes, chrome. quickopen uses [Chrome Apps v2](http://developer.chrome.com/trunk/apps/about_apps.html) for its UI.

Getting started
================================================================================

Get the code and **dont forget to init the submodules**.

    git clone https://github.com/natduca/quickopen.git
    git submodule update --init --recursive

Tell quickopen to index some directories...

      nduca: ~/quickopen $ ./quickopen add ~/Local/chrome
      nduca: ~/quickopen $ ./quickopen add ~/quickopen
      nduca: ~/quickopen $ ./quickopen ignore \*LayoutTests\*

Check quickopen's status:

      nduca: ~/quickopen $ ./quickopen rawsearch foo
      Database is not fully indexed. Wait a bit or try quickopen status

      nduca: ~/quickopen $ ./quickopen status
      Syncing: 17802 files found, 116 dirs pending

      nduca: ~/quickopen $ ./quickopen status
      up-to-date: 158553 files indexed; 2-threaded searches


VIM Setup
================================================================================

Using pathogen:

1. [http://github.com/tpope/vim-pathogen](http://github.com/tpope/vim-pathogen)
2. `git submodule add https://github.com/natduca/quickopen ~/.vim/bundle/quickopen`

Or, by hand in your `.vimrc`:

1. `source quickopen/plugin/quickopen.vim`

You're done! To open things, you've got a few options:

*  `:O` for the quickopen dialog
*  `:O somefile` to open the best match if its obvious, or the dialog if not.
*  `gf` or `c-w` to goto file

Emacs Setup
================================================================================


By hand, in your `.emacs`:

    (load "quickopen/elisp/quickopen.el")

Using site-lisp:

    git clone https://github.com/natduca/quickopen.git ~/.emacs/site-lisp


And if site-lisp isn't set up yet:

    (let ((site-lisp-dir (expand-file-name "~/.emacs/site-lisp")))
      (when (file-exists-p site-lisp-dir)
        (let ((default-directory site-lisp-dir))
          (normal-top-level-add-to-load-path '("."))
          (normal-top-level-add-subdirs-to-load-path))))

Consider binding `ff-find-other-file` to a hotkey if you haven't done
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


You're done! To use quickopen, use `M-S-o (meta-shift-o)` or `C-q`.


Visual SlickEdit Setup
================================================================================

1. Ensure that the directory containing quickopend is in your path.

2. Load the quickopen macro module by clicking Macro > Load Module..., and
    selecting slickedit/QuickOpen.e.

3. Now set up a key binding for quick open.
    - Click, Tools > Options...
    - Expand 'Keyboard and Mouse'
    - Select 'Key Bindings'
    - Type QuickOpen in the 'Search by command:' text box. If all goes well,
       this command will exist and be found.
    - Then click the 'Add..' button and bind to whichever keys you please,
       but I strongly recommend ctrl+shift+o for consistency with vim.

You're done. Use `C-O (ctrl-shift-o)` to open things.


Command Line Usage
================================================================================

      nduca: ~/quickopen $ ./quickedit
         <brings up a GUI for a picking a file,
          opens the picked file in $EDITOR>

If you want to hook into your favorite editor:

      nduca: ~/quickopen $ ./quickopen search --help
