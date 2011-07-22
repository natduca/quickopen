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
  (let ((true-load-file-name (file-truename load-file-name)))
    (substring true-load-file-name
               0
               (quickopen-strrchr true-load-file-name "/elisp"))))

(message (format "QuickOpen loaded at %s" quickopen-dir-base))

(global-set-key (kbd "M-O") (lambda ()
  (interactive "")
  (quickopen)))
(global-set-key (kbd "A-O") (lambda ()
  (interactive "")
  (quickopen)))
