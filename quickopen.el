(defun quickopen-run ()
  (with-temp-buffer 
    (let* ((prev-point (point)))
      (call-process (format "%s/%s" quickopen-dir-base "quickopen") nil t)
      (if (> (point) 1)
        (buffer-substring prev-point (- (point) prev-point))
      nil))))

(defun quickopen()
  (interactive "")
  (let* ((result (quickopen-run)))
    (when result
      (message (format "qo obtained %s" result))
      (find-file result))))

(defun quickopen-strrchr(x y) 
  (with-temp-buffer
    (insert x)
    (search-backward y)
    (- (point) 1)))

(setq quickopen-dir-base
  (substring load-file-name
    0
    (quickopen-strrchr load-file-name "/")))

(message (format "QuickOpen loaded at %s" quickopen-dir-base))

(global-set-key (kbd "M-O") (lambda ()
  (interactive "")
  (quickopen)))
(global-set-key (kbd "A-O") (lambda ()
  (interactive "")
  (quickopen)))
