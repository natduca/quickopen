# Copyright 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import curses
import curses.ascii as ascii
import message_loop
import message_loop_curses
import time
import os
import basename_ranker

from open_dialog import OpenDialogBase

def spad(s, w):
  if len(s) > w:
    return s[:w]
  elif len(s) == w:
    return s
  else:
    t = s
    while len(t) < w:
      t += ' '
    return t

class OpenDialogCurses(OpenDialogBase):
  def __init__(self, settings, options, db, initial_filter):
    OpenDialogBase.__init__(self, settings, options, db, initial_filter)
    message_loop_curses.on_terminal_readable.add_listener(self._on_readable)
    self._stdscr = message_loop_curses.get_stdscr()

    self._refresh_pending = False
    self._invalidate()

    self._status = ''
    self._update_border()

    self._update_filter_text()

    h,w = self._stdscr.getmaxyx()
    self._stdscr.hline(1, 0, '-', w)
    self._stdscr.hline(h - 3, 0, '-', w)
    
    self._selected_index = 0
    self._result_files = []
    self._result_ranks = []

    # The location of the "cursor" in the filter text "readline" area
    if self.should_position_cursor_for_replace:
      self._filter_text_point = 0
    else:
      self._filter_text_point = len(self._filter_text)

    curses.init_pair(1, 1, curses.COLOR_BLACK)

    # Uncomment to store keypresses to a logfile
    # This is for DEBUGGING purposes only.
    # self._keylog = open('/tmp/quickopen.keylog', 'w', False)

  def _update_border(self):
    status = 'QuickOpen: %s' % self._status
    h,w = self._stdscr.getmaxyx()
    self._stdscr.addstr(0, 0, status[:w])

  def _on_readable(self):
    kcode = self._stdscr.getch()
    k = curses.keyname(kcode)
    if k == '^[':
      n = self._stdscr.getch()
      nk = curses.keyname(n)
      kcode = kcode << 8 | n
      k = "M-%s" % curses.keyname(n)

    if hasattr(self, '_keylog'):
      self._keylog.write('k=[%10s] kcode=[%s]\n' % (k, kcode))

    if k == 'KEY_UP' or k == '^P':
      self._selected_index -= 1
      self._clamp_selected_index()
      self._update_results()
    elif k == 'KEY_DOWN' or k == '^N':
      self._selected_index += 1
      self._clamp_selected_index()
      self._update_results()
    elif k == '^G':
      self.on_done(True)
      return
    elif kcode == ascii.NL:
      self.on_done(False)
      return
    elif k == 'KEY_BACKSPACE' or k == '^?':
      if self._filter_text_point > 0:
        before = self._filter_text[0:self._filter_text_point]
        after = self._filter_text[self._filter_text_point:]
        self._filter_text = "%s%s" % (before[:-1], after)
        self._filter_text_point -= 1
        self._update_filter_text()
    elif k == '^D':
      before = self._filter_text[0:self._filter_text_point]
      after = self._filter_text[self._filter_text_point:]
      self._filter_text = "%s%s" % (before, after[1:])
      self._update_filter_text()
    elif k == '^A':
      self._filter_text_point = 0
      self._update_filter_text()
    elif k == '^E':
      self._filter_text_point = len(self._filter_text)
      self._update_filter_text()
    elif k == '^B' or k == 'KEY_LEFT':
      self._filter_text_point -= 1
      self._filter_text_point = max(0, min(self._filter_text_point, len(self._filter_text)))
      self._update_filter_text()
    elif k == '^F' or k == 'KEY_RIGHT':
      self._filter_text_point += 1
      self._filter_text_point = max(0, min(self._filter_text_point, len(self._filter_text)))
      self._update_filter_text()
    elif k == 'M-b':
      wordstarts = basename_ranker.BasenameRanker().get_starts(self._filter_text)
      wordstarts.append(len(self._filter_text))
      candidates = []
      for start in wordstarts:
        if start < self._filter_text_point:
          candidates.append(start)
      if len(candidates):
        self._filter_text_point = candidates[-1]
        self._filter_text_point = max(0, min(self._filter_text_point, len(self._filter_text)))
        self._update_filter_text()
    elif k == 'M-f':
      wordstarts = ranker.Ranker().get_starts(self._filter_text)
      wordstarts.append(len(self._filter_text))
      candidates = []
      for start in wordstarts:
        if start > self._filter_text_point:
          candidates.append(start)
      if len(candidates):
        self._filter_text_point = candidates[0]
        self._filter_text_point = max(0, min(self._filter_text_point, len(self._filter_text)))
        self._update_filter_text()
    elif k == '^K':
        before = self._filter_text[0:self._filter_text_point]
        self._filter_text = before
        self._update_filter_text()
    elif k == '^R':
      self.on_reindex_clicked()
    else:
      if not (k.startswith('^') or k.startswith('KEY_') or k.startswith('M-')):
        before = self._filter_text[0:self._filter_text_point]
        after = self._filter_text[self._filter_text_point:]
        self._filter_text = "%s%s%s" % (before, k, after)
        self._filter_text_point += 1
        self._update_filter_text()
        self.set_filter_text(self._filter_text)

  def _clamp_selected_index(self):
    if self._selected_index < 0:
      self._selected_index = 0
    if self._selected_index > len(self._result_files):
      self._selected_index = len(self._result_files) - 1

  def _invalidate(self):
    if self._refresh_pending:
      return
    self._refresh_pending = True
    message_loop.post_delayed_task(self._refresh, 0.005)

  def _refresh(self):
    self._refresh_pending = False
    tstart = "Filter: "
    t = tstart + self._filter_text
    h,w = self._stdscr.getmaxyx()
    self._stdscr.addstr(h - 2, 0, spad(t, w - 2))
    self._stdscr.move(h - 2, len(tstart) + self._filter_text_point)
    self._stdscr.refresh()

  def set_results_enabled(self, en):
    pass

  def set_status(self, status_text):
    self._status = status_text
    self._update_border()
    self._invalidate()

  # update the model based on result
  def update_results_list(self, files, ranks):
    self._result_files = files
    self._result_ranks = ranks
    self._clamp_selected_index()
    self._update_results()

  def _update_results(self):
    wh,ww = self._stdscr.getmaxyx()
   
    x = 1
    y = 2
    h = wh - 5
    w = ww - 2

    # update the screen
    for i in range(h):
      if i < len(self._result_files):
        f = self._result_files[i]
        bn = os.path.basename(f)
        p = os.path.dirname(f)
        l = "%2i   %40s   %s" % (self._result_ranks[i],
                                 bn,
                                 p)
        t = spad(l, w)
        if i == self._selected_index:
          a = curses.color_pair(1) | curses.A_REVERSE
        else:
          a = 0
        self._stdscr.addstr(y + i, x, t, a)
      else:
        t = spad('', w)
        self._stdscr.addstr(y + i, x, t, )

    self._invalidate()

  def _update_filter_text(self):
    self._invalidate()

  def get_selected_items(self):
    if self._selected_index < 0 or self._selected_index >= len(self._result_files):
      return []
    return [self._result_files[self._selected_index]]

  def destroy(self):
    pass
