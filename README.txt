Open files in Vim or Emacs quickly with fuzzy expressions and a live-updating
UI, even for directory-trees containing hundreds of thousands of files.

Fuzzy? When you enter "rwh", quickopen searches for things like
       RenderWidgetHost
       render-widget-host
       threaded_window_handler

The results are ranked by relevance. All in 30ms. So you can refine as you type.



Compared To?
===========================================================================
FuzzyFilter for Vim/FuzzyMatch for Emacs
  +:   Fast!!!!!!!!
  +:   Index maintained in-memory, but outside editor process
  +:   Reasonablly pretty GUI (even via ssh)
  +:   Same backend shared between emacs and vim
  -:   Doens't help when switching buffers

git ls-files
  +:   Search that Spans multiple projects, repositories, repository types
  +:   Faster
  -:   Doesn't support full regular expression matching goodness



Dependencies
================================================================================
Linux:
        python-gtk2

OSX:
        http://www.wxpython.org/download.php#stable
        wxPython 2.8-osx-unicode-2.6

Experimental:
        ./quickopen --curses 


VIM Bindings
================================================================================
0. Use pathogen, if you're not using it already:
      http://github.com/tpope/vim-pathogen
1a. Either of the following, depending on how your .vim is set up:
      git submodule add https://github.com/natduca/quickopen ~/.vim/bundle/quickopen
      git clone https://github.com/natduca/quickopen.git ~/.vim/bundle/


If you do things manually, the file you want vim to source is
quickopen/plugin/quickopen.vim



Emacs Bindings
================================================================================
Assuming you have ~/.emacs.d/site-lisp/, one of the following should work:
  git submodule add https://github.com/natduca/quickopen ~/.emacs/site-lisp
  git clone https://github.com/natduca/quickopen.git ~/.emacs/site-lisp

If you do things manually, the file you want emacs to find is
quickopen/elisp/quickopen.el

This usually does the trick:
  (let ((site-lisp-dir (expand-file-name "~/.emacs/site-lisp")))
    (when (file-exists-p site-lisp-dir)
      (let ((default-directory site-lisp-dir))
        (normal-top-level-add-to-load-path '("."))
        (normal-top-level-add-subdirs-to-load-path))))


Post-install configuration
================================================================================
 0. Start quickopend
      nduca: ~/quickopen $ ./quickopend&
      Starting quickopen daemon on port 10248

 1. Tell quickopen to index some directories...
      nduca: ~/quickopen $ ./quickopen add ~/chromium
      nduca: ~/quickopen $ ./quickopen add ~/quickopen
      nduca: ~/quickopen $ ./quickopen ignore \*LayoutTests\*

 2. Check quickopen's status:
      nduca: ~/quickopen $ ./quickopen rawsearch foo
      Database is not fully indexed. Wait a bit or try quickopen status

      nduca: ~/quickopen $ ./quickopen status
      Syncing: 17802 files found, 116 dirs pending

      nduca: ~/quickopen $ ./quickopen status
      up-to-date: 158553 files indexed; 2-threaded searches

Usage
================================================================================

  1. VIM:     C-O                   (ctrl-shift-o)
     Emacs:   M-S-o                 (meta-shift-o)

  2. Command line
      nduca: ~/quickopen $ ./quickopen
         <brings up a GUI for a picking a file,
          prints file picked to stdout once done>

  3. Command line, raw mode:
      nduca: ~/quickopen $ ./quickopen rawsearch render_widgethvw
      ~/chrome/src/content/browser/renderer_host/render_widget_host_view.h
      ~/chrome/src/chrome/browser/renderer_host/render_widget_host_view_gtk.h
      ~/chrome/src/chrome/browser/renderer_host/render_widget_host_view_views.h
      ~/chrome/src/chrome/browser/renderer_host/render_widget_host_view_win.h
      ~/chrome/src/chrome/browser/renderer_host/render_widget_host_view_mac.h

