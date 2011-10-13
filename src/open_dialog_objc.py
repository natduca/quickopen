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
import time
import logging
import message_loop
import os
import sys

from AppKit import *

from open_dialog import OpenDialogBase

class OpenDialogObjc(OpenDialogBase):
  def __init__(self, settings, options, db):
    OpenDialogBase.__init__(self, settings, options, db)
    message_loop.init_main_loop()
    size = NSMakeRect(0,0,800,400)
    self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
      size,
      NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask | NSMiniaturizableWindowMask,
      NSBackingStoreBuffered,
      False)
    self.window.setTitle_("TraceViewer")
    self.window.contentView().setAutoresizesSubviews_(True)

    
  def on_ok(self, event):
    self.on_done(False)

  def on_cancel(self, event):
    self.on_done(True)

  def set_status(self,status_text):
    self.status_text.SetLabel(status_text)

  def set_results_enabled(self,en):
    self._results_list.Enable(en)
    if not en:
      self._results_list.ClearAll()
    okbn = self.FindWindowById(wx.ID_OK)
    okbn.Enable(en)

  def update_results_list(self, files, ranks):
    self._results_list.ClearAll()
    self._results_list.InsertColumn(0, "Rank")
    self._results_list.InsertColumn(1, "File")
    self._results_list.InsertColumn(2, "Path")
    for i in range(len(files)):
      f = files[i]
      r = ranks[i]
      base = os.path.basename(f)
      path = os.path.dirname(f)
      i = self._results_list.InsertStringItem(sys.maxint, str(r))
      self._results_list.SetStringItem(i, 1, base)
      self._results_list.SetStringItem(i, 2, path)

    if len(files):
      self._results_list.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
    c1w = 200
    self._results_list.SetColumnWidth(0, 20)
    self._results_list.SetColumnWidth(1, 200)
    self._results_list.SetColumnWidth(2, self._results_list.GetSize()[0] - c1w)

  def move_selection(self, direction):
    raise Exception("Not implemented")

  def get_selected_index(self, favor_topmost=True):
    raise Exception("Not implemented")

  def get_selected_indices(self):
    raise Exception("Not implemented")

  def get_selected_items(self):
    raise Exception("Not implemented")
