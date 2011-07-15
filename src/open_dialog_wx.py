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
import re
import time
import logging
import os
import wx
import wx.lib.mixins.listctrl  as  listmix
import sys

from open_dialog_base import OpenDialogBase

class TestListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

class OpenDialogWx(wx.Dialog, OpenDialogBase):
  def __init__(self, settings, db):
    wx.Dialog.__init__(self, None, wx.ID_ANY, "Quick open...", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size=(1000,400))
    OpenDialogBase.__init__(self, settings, db)

    sizer = wx.BoxSizer(wx.VERTICAL)

    top_box = wx.BoxSizer(wx.HORIZONTAL)
    
    reset_bn = wx.Button(self, -1, "Reset database")
    top_box.Add(reset_bn)
    top_box.AddStretchSpacer(1)
    refresh_bn = wx.Button(self, -1, "Refresh")
    top_box.Add(refresh_bn)

    middle_box = wx.BoxSizer(wx.HORIZONTAL)
    self._results_list = TestListCtrl(self, -1,
                                      style=wx.LC_REPORT | wx.BORDER_NONE)
    middle_box.Add(self._results_list, 1, wx.ALIGN_CENTRE|wx.ALL|wx.EXPAND)

    

#    lower_sizer = wx.BoxSizer(wx.HORIZONTAL)
#    cancel_bn = wx.Button(self, wx.ID_CANCEL)
#    ok_bn = wx.Button(self, wx.ID_OK)
#    lower_sizer.Add(cancel_bn)
#    lower_sizer.Add((10,0), 0)
#    lower_sizer.Add(ok_bn)

    filter_box = wx.BoxSizer(wx.HORIZONTAL)
    self._filter_ctrl = wx.TextCtrl(self, -1, self._filter_text)
    self.Bind(wx.EVT_TEXT, self.on_evt_text, self._filter_ctrl)
    filter_box.Add(self._filter_ctrl, 1, wx.EXPAND)

    lower_sizer = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)

    sizer.Add(top_box, 0, wx.EXPAND|wx.BOTTOM, 8)
    sizer.Add(middle_box, 1, wx.GROW|wx.BOTTOM,8)
    sizer.Add(filter_box, 0, wx.GROW|wx.BOTTOM,7)
    sizer.Add(lower_sizer, 0, wx.ALIGN_RIGHT|wx.BOTTOM)

    outer_sizer = wx.BoxSizer(wx.VERTICAL)
    outer_sizer.Add(sizer, 1, wx.ALL | wx.EXPAND, 8)
    self.SetSizer(outer_sizer)
    
    self._filter_ctrl.SetFocus()

  def on_evt_text(self,event):
    self.set_filter_text(self._filter_ctrl.GetValue())

  def update_results_list(self, files):
    self._results_list.ClearAll()
    self._results_list.InsertColumn(0, "File")
    self._results_list.InsertColumn(1, "Path")
    for f in files:
      base = os.path.basename(f)
      path = os.path.dirname(f)
      i = self._results_list.InsertStringItem(sys.maxint, base)
      self._results_list.SetStringItem(i, 1, path)
    c1w = 200
    self._results_list.SetColumnWidth(0, 200)
    self._results_list.SetColumnWidth(1, self._results_list.GetSize()[0] - c1w)

  def get_selected_index(self):
    return self._results_list.GetNextSelected(-1)

def run(settings, db):
  app = wx.App(False)
  dlg = OpenDialogWx(settings, db)
  dlg.CenterOnScreen()
  val = dlg.ShowModal()
  if val == wx.ID_OK:
    print dlg.get_selected_index()
  dlg.Destroy()

if __name__ == "__main__":
  import db_test_base
  import settings
  import tempfile
  import temporary_daemon

  db_test_base = db_test_base.DBTestBase()
  db_test_base.setUp()
  daemon = temporary_daemon.TemporaryDaemon()
  client_settings_file = tempfile.NamedTemporaryFile()
  client_settings = settings.Settings(client_settings_file.name)
  db = daemon.db_proxy
  db.add_dir(db_test_base.test_data_dir)
  run(client_settings, db)
  db_test_base.tearDown()
  client_settings_file.close()
