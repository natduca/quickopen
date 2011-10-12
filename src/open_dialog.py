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
import json
import logging
import message_loop
import re
import os
import time

from trace_event import *

class OpenDialogBase(object):
  def __init__(self, settings, options, db):
    settings.register("filter_text", str, "")
    settings.register("query_log", str, "") 
    self._filter_text = settings.filter_text
    self._settings = settings
    self._db = db
    self._can_process_queries = False
    self._last_search_query = None
    self._pending_search = None
    self._options = options

  def set_can_process_queries(self, can_process):
    could_process = self._can_process_queries
    self._can_process_queries = can_process

    self.set_results_enabled(can_process)

  @trace
  def set_filter_text(self, text):
    self._filter_text = text
    if self._settings.query_log != "":
      try:
        f = open(os.path.expanduser(self._settings.query_log), 'a')
        f.write(json.dumps({"ts": time.time(), "query": text}))
        f.write("\n");
        f.close()
      except IOError:
        import traceback; traceback.print_exc()
        pass

  def on_tick(self,*args):
    def begin_search():
      self.set_status("DB Status: %s" % "searching")
      self._last_search_query = self._filter_text
      self._pending_search = self._db.search_async(self._last_search_query)

    def on_ready():
      try:
        res = self._pending_search.result
      except AsyncSearchError:
        res = None
      self._pending_search = None
      if res:
        self.update_results_list(res.hits,res.ranks)
      else:
        self.update_results_list([],[])
      self._pending_search = None

    def check_status():
      try:
        stat = self._db.status()
        status = stat.status
        enabled = stat.has_index
      except Exception, ex:
        status = "quickopend not running"
        enabled = False
      self.set_status("DB Status: %s" % status)
      self.set_can_process_queries(enabled)

    if self._pending_search:
      self.set_status("DB Status: %s" % "searching")
      if self._pending_search.ready:
        on_ready()

    # re-check the self._pending_search since we might have cleared it
    if not self._pending_search:
      # kick off a query
      if self._filter_text != self._last_search_query and self._can_process_queries:
        begin_search()
      else:
        # poll status
        check_status()

  def on_done(self, canceled):
    self._settings.filter_text = self._filter_text.encode('utf8')
    if canceled:
      res = []
    else:
      res = self.get_selected_items()
    if self._options.ok and not canceled:
      print "OK"
    print "\n".join(res)
    message_loop.quit_main_loop() # end of the line, no further output will happen

def run(settings, options, db):
  def _pick_open_dialog():
    if message_loop.is_gtk:
      return __import__("src.open_dialog_gtk", {}, {}, True).OpenDialogGtk
    elif message_loop.is_wx:
      return __import__("src.open_dialog_wx", {}, {}, True).OpenDialogWx
    else:
      raise "Unsupported"

  def go():
    OpenDialog = _pick_open_dialog()
    dlg = OpenDialog(settings, options, db)

  message_loop.post_task(go)
  message_loop.run_main_loop()
