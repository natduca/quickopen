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
import os

from db_index import DBIndex
from db_indexer import DBIndexer
from dir_cache import DirCache
from dyn_object import DynObject
from event import Event

DEFAULT_IGNORES=[
  ".*",
  ".o",
  ".obj",
  ".pyc",
  ".pyo",
]

"""
Exception thrown when a search fails due to the DB being unsyncd
"""
class NotSyncdException(Exception):
  def __init__(self,*args):
    Exception.__init__(self, *args)

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
    self.needs_sync = Event() # fired when the database gets dirtied and needs syncing
    self._dirty = True # whether the settings have dirtied the db
    self._pending_indexer = None # non-None if a DBIndex is running
    self._cur_index = None # the last DBIndex object --> actually runs the searches

    self._dir_cache = DirCache() # thread only state


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
    d = os.path.abspath(d)

    cur = list(self.settings.dirs)
    if d in cur:
      return

    # commit change
    cur.append(d)
    self.settings.dirs = cur  # triggers _on_settings_dirs_changed
    return self.dirs[-1]

  def delete_dir(self, d):
    if type(d) != DBDir:
      raise Exception("Expected DBDir")
    cur = list(self.settings.dirs)
    if d.path not in cur:
      raise Exception("not found")
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
  def is_syncd(self):
    return self.sync_status().is_syncd

  def _set_dirty(self):
    if self._pending_indexer:
      self._pending_indexer = None
    was_dirty = self._dirty
    self._dirty = True
    if not was_dirty:
      self.needs_sync.fire()

  def sync_status(self):
    if self._dirty:
      if self._pending_indexer:
        status = "syncing: %s" % self._pending_indexer.progress
      else:
        status = "dirty but not synchronized"
    else:
      status = "up-to-date: %s" % self._cur_index.status

    return DynObject({"is_syncd": not self._dirty,
                      "status": status})

  def step_sync(self):
    if self._pending_indexer:
      if self._pending_indexer.complete:
        self._cur_index = DBIndex(self._pending_indexer)
        self._pending_indexer = None
        self._dirty = False
      else:
        self._pending_indexer.index_a_bit_more()
      return

    # start new sync
    self._dir_cache.set_ignores(self.settings.ignores)
    self._pending_indexer = DBIndexer(self.settings.dirs, self._dir_cache)

  def sync(self):
    """Ensures database index is up-to-date"""
    while self._dirty:
      self.step_sync()

  ###########################################################################
  def search(self,query):
    if not self.is_syncd:
      self.step_sync()
      # step sync might change the db sync status
      if not self.is_syncd:
        raise NotSyncdException("DB not syncd")

    return self._cur_index.search(query)

