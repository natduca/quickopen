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
import message_loop
import time
import os
import message_loop_curses

from open_dialog import OpenDialogBase

class OpenDialogCurses(OpenDialogBase):
  def __init__(self, settings, options, db):
    OpenDialogBase.__init__(self, settings, options, db)
    message_loop_curses.on_terminal_readable.add_listener(self._on_readable)
    self.stdscr = message_loop_curses.get_stdscr()

  def _on_readable(self):
    print "got", self.stdscr.getch()

  def set_results_enabled(self, en):
    pass

  def set_status(self, status_text):
    pass

  # update the model based on result
  def update_results_list(self, files, ranks):
    if len(files) == 0:
      pass

  def get_selected_items(self):
    return []
