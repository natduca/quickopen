;;; quickopen.el --- Bindings to open files with quickopen
;;
;; Copyright 2011 Google Inc.
;;
;; Licensed under the Apache License, Version 2.0 (the "License");
;; you may not use this file except in compliance with the License.
;; You may obtain a copy of the License at
;;
;;      http://www.apache.org/licenses/LICENSE-2.0
;;
;; Unless required by applicable law or agreed to in writing, software
;; distributed under the License is distributed on an "AS IS" BASIS,
;; WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
;; See the License for the specific language governing permissions and
;; limitations under the License.

(provide 'quickopen)

;; This provides a find-file implementation that will call out to
;; quickopen for actual selection.
;;
;;    (quickopen-find-file)
;;
;; The default keybinding is to C-q
;;
;; In a GUI-based emacs, the regular quickopen GUI is used.
;;
;; In a terminal emacs, the quickopen curses UI is used.
;;
;; Note that in curses mode, (quickopen-find-file) is asynchronous.
;; Patches welcome to rework it to use a minibuffer.

(defcustom quickopen-override-ff-find t
  "If non-nil, uses quickopen to service ff-find-other commands."
  :type 'boolean
  :group 'quickopen)

(defcustom quickopen-prefer-curses nil
  "If non-nil, quickopen will prefer the curses UI all the time"
  :type 'boolean
  :group 'quickopen)


(defun quickopen-has-gui ()
  (when (fboundp 'window-system)
    (when window-system
      1)))

;; Default keybindings... these may smell bad. Patches welcome!
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(if (quickopen-has-gui)
    (progn
      (global-set-key (kbd "C-q") (lambda ()
                                    (interactive "")
                                    (quickopen-find-file)))
      (global-set-key (kbd "M-O") (lambda ()
                                    (interactive "")
                                    (quickopen-find-file)))
      (global-set-key (kbd "A-O") (lambda ()
                                    (interactive "")
                                    (quickopen-find-file)))
      (global-set-key (kbd "s-O") (lambda ()
                                    (interactive "")
                                    (quickopen-find-file)))
      )
  (progn
    (global-set-key (kbd "C-q") (lambda ()
                                  (interactive "")
                                  (quickopen-find-file)))
    )
  )

;; Helper functions
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(defun quickopen-strrchr(x y)
  (with-temp-buffer
    (insert x)
    (search-backward y)
    (- (point) 1)))

(defun quickopen-filter(predicate list)
  "Return items in LIST satisfying."
  (delq nil
	(mapcar (lambda (x)
		  (and (funcall predicate x)
		       x
		       )
		  )
		list
		)
	)
  )

(setq quickopen-dir-base
  (let ((true-load-file-name (file-truename load-file-name)))
    (substring true-load-file-name
               0
               (quickopen-strrchr true-load-file-name "/elisp"))))
(message (format "QuickOpen loaded at %s" quickopen-dir-base))

(defun quickopen-get-open-filenames-string()
  (mapconcat 'identity
             (mapcar (lambda (x) 
                       (with-temp-buffer
                         (insert (buffer-file-name x))
                         (goto-char 0)
                         (while (search-forward ":" nil t)
                           (replace-match "\\:" nil t))
                         (buffer-substring (point-min) (point-max))
                         )
                       )
                     (quickopen-filter (lambda (x) (buffer-file-name x))
                             (buffer-list)
                             )
                     )
             ":"
             )
  )

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(defun quickopen-find-file-using-gui(&optional query skip-ui-if-exact-match other-window)
  (interactive "")
  (let (res
        (current-buffer-filename (buffer-file-name (current-buffer)))
        )
    (setq res (with-temp-buffer
                (let ((open-buffers (quickopen-get-open-filenames-string))
                      (args (list (format "%s/%s" quickopen-dir-base "quickopen") nil t nil "prelaunch" "search" "--ok" "--lisp-results")))
                  (when (> (length open-buffers) 0)
                    (setq args (append args (list "--open-filenames" open-buffers)))
                    )
                  (when skip-ui-if-exact-match
                    (setq args (append args '("--skip-ui-if-exact-match")))
                    )
                  (when current-buffer-filename
                    (setq args (append args (list "--current-filename" current-buffer-filename)))
                    )
                  (when query
                    (setq args (append args (list query)))
                    )
                  (apply 'call-process  args)
                  )
                ;; There is a delay between call-process and the external UI
                ;; taking over input. Discard any buffered characters that happened during this time.
                (discard-input)
                (quickopen-get-results-from-current-buffer)
                )
          )
    (mapcar (lambda (file)
              (if (not other-window)
                  (find-file file)
                (find-file-other-window file)
                )
              )
            res)
    )
  )

(defvar quickopen-current-buffer nil)
(defvar quickopen-current-buffer-open-result-in-other-window nil)
(defvar quickopen-old-window-configuration nil)

(defun quickopen-find-file-using-curses (&optional query skip-ui-if-exact-match other-window)
  (if quickopen-current-buffer
      (progn
        (message "Already open, cannot continue.")
        )
    (let ((program (format "%s/%s" quickopen-dir-base "quickopen"))
          (current-buffer-filename (buffer-file-name (current-buffer)))
          )
      (setq quickopen-old-window-configuration (current-window-configuration))
      (delete-other-windows)
      (when (get-buffer "*quickopen*")
        (with-current-buffer "*quickopen*"
          (delete-region (point-min) (point-max))
          )
        )
      (setq quickopen-current-buffer 
            (let ((open-buffers (quickopen-get-open-filenames-string))
                  (args (list "quickopen" program nil "search" "--curses" "--ok" "--lisp-results")))
              (when (> (length open-buffers) 0)
                (setq args (append args (list "--open-filenames" open-buffers)))
                )
              (when skip-ui-if-exact-match
                (setq args (append args '("--skip-ui-if-exact-match")))
                )
              (when current-buffer-filename
                (setq args (append args (list "--current-filename" current-buffer-filename)))
                )
              (when query
                (setq args (append args (list query)))
                )
              (apply 'make-term  args)
              )
            )
      (setq quickopen-current-buffer-open-result-in-other-window other-window)
      (set-buffer quickopen-current-buffer)
      (term-mode)
      (term-char-mode)
      (switch-to-buffer quickopen-current-buffer)

      ;; turn off stuff that screws up term mode
      (when (fboundp 'show-ws-highlight-trailing-whitespace)
        (when show-ws-highlight-trailing-whitespace-p
          (toggle-show-trailing-whitespace-show-ws)
          )
        )
      )
    )
  )

;; override linum-on in quickopen buffer since it breaks term mode
(when (fboundp 'linum-on)
  (defadvice linum-on (after quickopen-after-linum-on)
    (when (string= "*quickopen*" (buffer-name))
      (linum-mode 0)
      )
    )
  (ad-activate 'linum-on)
  )

(defun quickopen-get-results-from-current-buffer()
  (let (x y res)
    (goto-char (point-max))
    (setq x (search-backward-regexp "OK\n" nil t))
    (setq y (search-forward-regexp "\n\n" nil t))
    (if x
        (progn
          (setq x (+ x 3))
          (setq res (buffer-substring-no-properties x y))
          (setq res (replace-regexp-in-string "\n" "" res)) ;; get rid of newlines
          (read res)
          )
      nil
      )
    )
  )

(defun quickopen-find-file-using-curses-exited (process-name msg)
  (let ((res (quickopen-get-results-from-current-buffer)))
    ;; Kill old buffer later --- we're inside the proc-death function so killing it 
    ;; now will make term-mode cry.
    (run-at-time "0.01 sec"
                 nil
                 (lambda (buf)
                   (kill-buffer buf)
                   )
                 quickopen-current-buffer
                 )
    ;; Clear the buffer flag immediately so that quickopen-find-file-using-curses understands
    ;; that it can create a new buffer.
    (setq quickopen-current-buffer nil)

    ;; restore window config
    (set-window-configuration quickopen-old-window-configuration)
    (setq quickopen-old-window-configuration nil)

    ;; open stuff up
    (when res
      (mapcar (lambda (file)
                (if (not quickopen-current-buffer-open-result-in-other-window)
                    (find-file file)
                  (find-file-other-window file)
                  )
                )
              res
              )
      )
    )
  )

(defadvice term-handle-exit (after quickopen-term-handle-exit (process-name msg))
  (when (eq (current-buffer) quickopen-current-buffer)
    (quickopen-find-file-using-curses-exited process-name msg)
    )
  )
(ad-activate 'term-handle-exit)

;; Actual quickopen find function
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(defun quickopen-find-file (&optional query skip-ui-if-exact-match other-window)
  "Opens a file using quickopen. Note, this is currently asynchronous in terminal mode."
  (if (and (quickopen-has-gui) (not quickopen-prefer-curses))
      (quickopen-find-file-using-gui query skip-ui-if-exact-match other-window)
    (quickopen-find-file-using-curses query skip-ui-if-exact-match other-window)
    )
  )

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Can only hook ff-find in GUI mode because curses mode quickopen is
;; asynchronous.
(when (and quickopen-override-ff-find (quickopen-has-gui))
  (defadvice ff-get-file (around quickopen-ff-get-file (search-dirs filename-template &optional suffix-list other-window))
    (message "ff-get-file-quickopen-wrapper")
    (setq ad-return-value 
          (let ((filename (ff-get-file-name search-dirs filename-template suffix-list)))
            (cond
             ((not filename)
              (message "quickopen fallback")
              (quickopen-find-file filename-template t other-window)
              t)

             ((bufferp (get-file-buffer filename))
              (ff-switch-to-buffer (get-file-buffer filename) other-window)
              filename)

             ((file-exists-p filename)
              (ff-find-file filename other-window nil)
              filename)
             )
            )
          )
    )
    (ad-activate 'ff-get-file)
  )
