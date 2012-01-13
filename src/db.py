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
import hashlib
import logging
import os

import daemon
from db_index import DBIndex, DBIndexSearchResult
from db_indexer import DBIndexer
from dir_cache import DirCache
from event import Event
from trace_event import *

DEFAULT_IGNORES=[
  ".*",
  "*.o",
  "*.obj",
  "*.pyc",
  "*.pyo",
  "*.o.d",
  "#*",
]

class DBException(daemon.SilentException):
  pass

class DBStatus(object):
  def __init__(self):
    self.is_up_to_date = False
    self.has_index = False
    self.status = "Unknown"

  def as_dict(self):
    return {"is_up_to_date": self.is_up_to_date,
            "has_index": self.has_index,
            "status": self.status}

  @staticmethod
  def from_dict(d):
    s = DBStatus()
    s.is_up_to_date = d["is_up_to_date"]
    s.has_index = d["has_index"]
    s.status = d["status"]
    return s

class DBDir(object):
  def __init__(self, d):
    self.path = d
    self.id = hashlib.md5(d).hexdigest()

  def __repr__(self):
    return "DBDir(%s)" % self.path

  def __getstate__(self):
    return {"id": self.id,
            "path": self.path}

  def __cmp__(self, other):
    if type(other) != DBDir:
      return 1
    return cmp(self.path, other.path)

class DB(object):
  def __init__(self, settings):
    self.settings = settings
    self.needs_indexing = Event() # fired when the database gets dirtied and needs syncing
    self._pending_indexer = None # non-None if a DBIndex is running
    self._cur_index = None # the last DBIndex object --> actually runs the searches

    self._dir_cache = DirCache() # thread only state

    # if we are currently looking for changed dirs, this is the iterator
    # directories remaining to be checked
    self._pending_up_to_date_generator = None 

    self.settings.register('dirs', list, [], self._on_settings_dirs_changed)
    self._on_settings_dirs_changed(None, self.settings.dirs)

    self.settings.register('ignores', list, [], self._on_settings_ignores_changed)
    if self.settings.ignores == []:
	self.settings.ignores = DEFAULT_IGNORES;

    self._on_settings_ignores_changed(None, self.settings.ignores)

  ###########################################################################

  def _on_settings_dirs_changed(self, old, new):
    self._dirs = map(lambda d: DBDir(d), new)
    self._set_dirty()

  @property
  def dirs(self):
    return list(self._dirs)

  def add_dir(self, d):
    real_d = os.path.realpath(d)

    cur = list(self.settings.dirs)
    if real_d in cur:
      raise DBException("Directory %s exists already as %s" % (d, real_d))

    # commit change
    cur.append(real_d)
    self.settings.dirs = cur  # triggers _on_settings_dirs_changed
    return self.dirs[-1]

  def delete_dir(self, d):
    if type(d) != DBDir:
      raise Exception("Expected DBDir")
    cur = list(self.settings.dirs)
    if d.path not in cur:
      raise DBException("not found")
    cur.remove(d.path)
    self.settings.dirs = cur # triggers _on_settings_dirs_changed

  ###########################################################################

  def _on_settings_ignores_changed(self, old, new):
    self._set_dirty()

  @property
  def ignores(self):
    return list(self.settings.ignores)

  def ignore(self,pattern):
    i = list(self.settings.ignores)
    if pattern in i:
      return
    i.append(pattern)
    self.settings.ignores = i

  def unignore(self,pattern):
    i = list(self.settings.ignores)
    i.remove(pattern)
    self.settings.ignores = i

  ###########################################################################

  @property
  def has_index(self):
    return self._cur_index != None

  @property
  def is_up_to_date(self):
    return self._pending_indexer == None

  def check_up_to_date(self):
    if not self.is_up_to_date:
      return False
    import time
    self.check_up_to_date_a_bit_more()
    while self._pending_up_to_date_generator:
      self.check_up_to_date_a_bit_more()

  @trace
  def check_up_to_date_a_bit_more(self):
    if not self.is_up_to_date:
      return

    if self._pending_up_to_date_generator == None:
      logging.debug("Starting to check for changed directories.")
      self._pending_up_to_date_generator = self._dir_cache.iterdirnames().__iter__()

    for i in range(10):
      try:
        d = self._pending_up_to_date_generator.next()
      except StopIteration:
        self._pending_up_to_date_generator = None
        logging.debug("Done checking for changed directories.")
        break
      if self._dir_cache.listdir_with_changed_status(d)[1]:
        logging.debug("Change detected in %s!", d)
        self._pending_up_to_date_generator = None
        self._set_dirty()
        break

  def begin_reindex(self):
    self._set_dirty()

  def _set_dirty(self):
    was_indexing = self._pending_indexer != None
    if self._pending_indexer:
      self._pending_indexer = None
    self._pending_indexer = 1 # set to 1 as indication to step_indexer to create new indexer
    if not was_indexing:
      self.needs_indexing.fire()

  @trace
  def status(self):
    if self._pending_indexer:
      if isinstance(self._pending_indexer, DBIndexer): # is an integer briefly between _set_dirty and first step_indexer
        if self._cur_index:
          status = "syncing: %s, %s" % (self._pending_indexer.progress, self._cur_index.status)
        else:
          status = "first-time sync: %s" % self._pending_indexer.progress
      else:
        status = "sync scheduled"
    else:
      if self._cur_index:
        status = "up-to-date: %s" % self._cur_index.status
      else:
        status = "sync required"

    res = DBStatus()
    res.is_up_to_date = self.is_up_to_date
    res.has_index = self.has_index
    res.status = status
    return res

  @trace
  def step_indexer(self):
    if not self._pending_indexer:
      return

    if not isinstance(self._pending_indexer, DBIndexer):
      self._dir_cache.set_ignores(self.settings.ignores)
      self._pending_indexer = DBIndexer(self.settings.dirs, self._dir_cache)

    if self._pending_indexer.complete:
      self._cur_index = DBIndex(self._pending_indexer)
      self._pending_indexer = None
    else:
      self._pending_indexer.index_a_bit_more()

  def sync(self):
    """Ensures database index is up-to-date"""
    self.check_up_to_date()
    while self._pending_indexer:
      self.step_indexer()

  ###########################################################################
  def _empty_result(self):
    return DBIndexSearchResult()

  @trace
  def search(self, query, max_hits = -1):
    if self._pending_indexer:
      self.step_indexer()
      # step sync might change the db sync status
      if not self._cur_index:
        return self._empty_result()

    if query == '':
      return self._empty_result()

    if max_hits == -1:
      return self._cur_index.search(query)
    else:
      return self._cur_index.search(query, max_hits)
