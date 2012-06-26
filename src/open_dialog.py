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
import db_proxy
import json
import logging
import message_loop
import re
import os
import query
import sys
import time

from db_status import DBStatus
from trace_event import *

TICK_RATE_WHEN_SEARCHING = 0.005
TICK_RATE_WHEN_UP_TO_DATE = 0.025
TICK_RATE_WHEN_NOT_UP_TO_DATE = 0.2

class OpenDialogBase(object):
  @tracedmethod
  def __init__(self, options, db, initial_filter = None):
    self._filter_text = ""
    if initial_filter:
      self._filter_text = initial_filter
    self._db = db
    self._frontend_status = None
    self._backend_status = DBStatus()
    self._can_process_queries = False
    self._db_is_up_to_date = True
    self._last_search_query = None
    self._pending_search = None
    self._options = options
    self._print_results_cb = None
    if initial_filter:
      self.should_position_cursor_for_replace = False
    else:
      self.should_position_cursor_for_replace = True

    # First tick should be fast.
    message_loop.post_delayed_task(self.on_tick, 0)

  @property
  def print_results_cb(self):
    """When results from the dialog are available, this callback is called.
    The callback is of the form (results, canceled)
    """
    return self._print_results_cb

  @print_results_cb.setter
  def print_results_cb(self, cb):
    self._print_results_cb = cb

  def set_can_process_queries(self, can_process):
    could_process = self._can_process_queries
    self._can_process_queries = can_process

    self.set_results_enabled(can_process)

  @tracedmethod
  def set_filter_text(self, text):
    self._filter_text = text

  def on_reindex_clicked(self):
    self._db.begin_reindex()

  def on_badresult_clicked(self):
    # get a debug version of the query
    q = self._create_query()
    q.debug = True
    result = self._db.search(q)
    badresult = {"query": q.as_dict(),
                 "result": result.as_dict()}
    import json
    badresult_text = json.dumps(badresult, indent=2)
    # TODO(enne): file a bug using badreuslt_text

  @property
  def frontend_status(self):
    return self._frontend_status

  @frontend_status.setter
  def frontend_status(self, status):
    self._frontend_status = status
    self.status_changed()

  @property
  def backend_status(self):
    return self._backend_status

  @backend_status.setter
  def backend_status(self, status):
    self._db_is_up_to_date = status.is_up_to_date
    self._can_process_queries = status.has_index and status.running
    self._backend_status = status
    self.status_changed()

  @property
  def status_text(self):
    if self.frontend_status:
      return "%s (%s)" % (self._backend_status.status, self._frontend_status)
    else:
      return "%s" % self._backend_status.status

  def _create_query(self):
    q = query.Query(self._filter_text)
    if self._options.current_filename:
      q.current_filename = self._options.current_filename
    if self._options.open_filenames:
      q.open_filenames = self._options.open_filenames
    return q

  @tracedmethod
  def on_tick(self,*args):
    @traced
    def begin_search():
      self.frontend_status = "searching"

      q = self._create_query()
      self._pending_search = self._db.search_async(q)
      self._last_search_query = q

    @traced
    def on_ready():
      try:
        res = self._pending_search.result
      except db_proxy.AsyncSearchError:
        res = None
      self.frontend_status = None
      self._pending_search = None
      trace_begin("update_results_list")
      if res:
        self.update_results_list(res.filenames,res.ranks)
      else:
        self.update_results_list([],[])
      trace_end("update_results_list")
      self._pending_search = None

    @traced
    def update_backend_status():
      self.backend_status = self._db.status()

    if self._pending_search:
      if self._pending_search.ready:
        on_ready()

    # re-check the self._pending_search since we might have cleared it
    if not self._pending_search:
      # kick off a query
      if self._last_search_query:
        need_to_begin_search = self._filter_text != self._last_search_query.text
      else:
        need_to_begin_search = True

      if need_to_begin_search and self._can_process_queries:
        begin_search()
      else:
        # poll backend status
        update_backend_status()

    # renew the tick
    if self._pending_search:
      message_loop.post_delayed_task(self.on_tick, TICK_RATE_WHEN_SEARCHING)
    elif self._db_is_up_to_date:
      message_loop.post_delayed_task(self.on_tick, TICK_RATE_WHEN_UP_TO_DATE)
    else:
      message_loop.post_delayed_task(self.on_tick, TICK_RATE_WHEN_NOT_UP_TO_DATE)

  # When someone knows exactly what they want, they are often familiar with what
  # to type, and so have typed it exactly and completely, possibly before the
  # GUI even was fully up. At that point, there may be a search pending, and that
  # search may not include all the characters that they typed .E.g:
  #   input: ab
  #                we start a query
  #   input: cd <enter>
  #                on_done called
  #
  # Their intent is us opening the first hit for abcd. To achieve this,
  # we need to wait until the current query is done. This will begin a new query
  # we for 'cd' which we will then wait for as well.
  @traced
  def _wait_for_pending_search_complete(self, wait_again=True):
    if not self._pending_search:
      return
    start_wait = time.time()
    while not self._pending_search.ready and time.time() < start_wait + 1:
      time.sleep(0.05)
    self.on_tick()
    if wait_again and self._pending_search:
      return self._wait_for_pending_search_complete(False)

  @traced
  def on_done(self, canceled):
    if canceled:
      res = []
    else:
      self._wait_for_pending_search_complete()
      res = self.get_selected_items()

      # If nothing was matched on the final search, leave the UI up.
      if len(res) == 0:
        return

    if self._print_results_cb:
      self._print_results_cb(res, canceled)
    message_loop.quit_main_loop() # end of the line, no further output will happen

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
