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
import message_loop

def _pick_open_dialog():
  if message_loop.is_gtk:
    return __import__("src.open_dialog_gtk", {}, {}, True).OpenDialogGtk
  elif message_loop.is_wx:
    return __import__("src.open_dialog_wx", {}, {}, True).OpenDialogWx
  elif message_loop.is_curses:
    return __import__("src.open_dialog_curses", {}, {}, True).OpenDialogCurses
  elif message_loop.is_objc:
    return __import__("src.open_dialog_objc", {}, {}, True).OpenDialogObjc
  else:
    raise Exception("Unrecognized message loop type.")
OpenDialog = _pick_open_dialog()

def run(options, db, initial_filter, print_results_cb = None):
  def go():
    dlg = OpenDialog(options, db, initial_filter)
    if print_results_cb:
      dlg.print_results_cb = print_results_cb

  message_loop.post_task(go)
  message_loop.run_main_loop()
