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

(defvar quickopen-prefer-curses nil
  "Set this to t in order to have quickopen prefer curses UI all
the time")

(defun quickopen-gui()
  (interactive "")
  (let (res)
    (setq res (with-temp-buffer
                (call-process (format "%s/%s" quickopen-dir-base "quickopen") nil t nil "prelaunch" "search" "--ok" "--lisp-results")
                (discard-input) ;; needed because call-process can take a WHILE
                (quickopen-get-results-from-current-buffer)
                )
          )
    (mapcar (lambda (file)
              (find-file file)
              )
            res)
    )
  )

(defun quickopen-strrchr(x y)
  (with-temp-buffer
    (insert x)
    (search-backward y)
    (- (point) 1)))

(setq quickopen-dir-base
  (let ((true-load-file-name (file-truename load-file-name)))
    (substring true-load-file-name
               0
               (quickopen-strrchr true-load-file-name "/elisp"))))

(message (format "QuickOpen loaded at %s" quickopen-dir-base))

(defun quickopen-has-gui ()
  (when (fboundp 'window-system)
    (when window-system
      1)))

(defvar quickopen-current-buffer nil)
(defvar quickopen-old-window-configuration nil)

(defun quickopen-curses ()
  (if quickopen-current-buffer
      (progn
        (message "Already open, cannot continue.")
        )
    (let ((program (format "%s/%s" quickopen-dir-base "quickopen"))
          )
      (setq quickopen-old-window-configuration (current-window-configuration))
      (delete-other-windows)
      (when (get-buffer "*quickopen*")
        (with-current-buffer "*quickopen*"
          (delete-region (point-min) (point-max))
          )
        )
      (setq quickopen-current-buffer (make-term "quickopen" program nil "--curses" "--ok" "--lisp-results"))
      (set-buffer quickopen-current-buffer)
      (term-mode)
      (term-char-mode)
      (switch-to-buffer quickopen-current-buffer)
      )
    )
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

(defun quickopen-curses-exited (process-name msg)
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
    ;; Clear the buffer flag immediately so that quickopen-curses understands
    ;; that it can create a new buffer.
    (setq quickopen-current-buffer nil)

    ;; restore window config
    (set-window-configuration quickopen-old-window-configuration)
    (setq quickopen-old-window-configuration nil)

    ;; open stuff up
    (when res
      (mapcar (lambda (file)
                (find-file file)
                )
              res
              )
      )
    )
  )

(defadvice term-handle-exit (after quickopen-term-handle-exit (process-name msg))
  (when (eq (current-buffer) quickopen-current-buffer)
    (quickopen-curses-exited process-name msg)
    )
  )
(ad-activate 'term-handle-exit)


(if (quickopen-has-gui)
    (progn
      (global-set-key (kbd "M-O") (lambda ()
                                    (interactive "")
                                    (quickopen-gui)))
      (global-set-key (kbd "A-O") (lambda ()
                                    (interactive "")
                                    (quickopen-gui)))
      (global-set-key (kbd "s-O") (lambda ()
                                    (interactive "")
                                    (quickopen-gui)))
      )
  (progn
      (global-set-key (kbd "ESC O") (lambda ()
                                    (interactive "")
                                    (quickopen-curses)))
    )
  )