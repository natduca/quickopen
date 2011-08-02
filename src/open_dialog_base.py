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
# limitaions under the License.
import json
import logging
import re
import os
import time

class OpenDialogBase(object):
  def __init__(self, settings, db):
    settings.register("filter_text", str, "")
    settings.register("query_log", str, "") 
    self._filter_text = settings.filter_text
    self._settings = settings
    self._db = db
    self._can_process_queries = False
    self._last_search_query = None
    self._pending_search = None

  def set_can_process_queries(self, can_process):
    could_process = self._can_process_queries
    self._can_process_queries = can_process

    self.set_results_enabled(can_process)
    
  def just_before_closed(self):
    self._settings.filter_text = self._filter_text

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

  def rescan(self):
    self._db.sync()

  def on_tick(self,*args):
    if self._pending_search:
      self.set_status("DB Status: %s" % "searching")
      if self._pending_search.ready:
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

    # re-check the self._pending_search since we might have cleared it
    if not self._pending_search:
      # kick off a query
      if self._filter_text != self._last_search_query and self._can_process_queries:
        self.set_status("DB Status: %s" % "searching")
        self._last_search_query = self._filter_text
        self._pending_search = self._db.search_async(self._last_search_query)
      else:
        # poll status
        try:
          stat = self._db.sync_status()
          status = stat.status
          enabled = stat.is_syncd
        except Exception, ex:
          status = "quickopend not running"
          enabled = False
        self.set_status("DB Status: %s" % status)
        self.set_can_process_queries(enabled)
