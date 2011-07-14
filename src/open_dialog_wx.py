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

from open_dialog_base import OpenDialogBase

class OpenDialogWx(wx.Frame, OpenDialogBase):
  def __init__(self, settings, db):
    wx.Frame.__init__(self, None, wx.ID_ANY, "QuickOpen")
    OpenDialogBase.__init__(self, settings, db)
    self.Show(True)

def run(settings, db):
  app = wx.App(False)
  dlg = OpenDialogWx(settings, db)
  app.MainLoop()

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
