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
import collections
import fnmatch
import os
import re
import hashlib

DEFAULT_IGNORE=[
  ".*",
]

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
    self._dir_cache = _DirCache()
    self._dirty = True

    self.settings.register('dirs', list, [], self._on_settings_dirs_changed)
    self._on_settings_dirs_changed(None, self.settings.dirs)

    self.settings.register('ignores', list, DEFAULT_IGNORE, self._on_settings_ignores_changed)
    self._on_settings_ignores_changed(None, self.settings.ignores)

  def _on_settings_dirs_changed(self, old, new):
    self._dirs = map(lambda d: DBDir(d), new)
    self._set_dirty()

  def _on_settings_ignores_changed(self, old, new):
    self._dir_cache.set_ignores(new)
    self._set_dirty()

  def _set_dirty(self):
    self._dirty = True

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
    return self.sync_status()['is_syncd']

  def sync_status(self):
    return {"is_syncd": not self._dirty,
            "stauts": "unsyncd"}

  def sync(self):
    """Ensures database index is up-to-date"""
    if not self._dirty:
      return
    sync = _DBSync(self.settings.dirs, self._dir_cache)
    sync.run()
    self._files = sync.files
    self._dirty = False

  def search(self,query_regex):
    rc = re.compile(query_regex)

    if not self.is_syncd:
      raise Exception("DB not syncd")

    res = []
    truncated = False
    for x in self._files:
      if rc.search(x):
        res.append(x)
    return res

class _DirEnt(object):
  def __init__(self, st_mtime, ents):
    self.st_mtime = st_mtime
    self.ents = ents

class _DirCache(object):
  def __init__(self):
    self.dirs = dict()
    self.rel_to_real = dict()
    self.ignores = []

  def set_ignores(self, ignores):
    self.dirs = dict()
    self.ignores = ignores

  def reset_realpath_cache(self):
    self.rel_to_real = dict()

  def realpath(self, d):
    if d in self.rel_to_real:
      return self.rel_to_real[d]
    else:
      r = os.path.realpath(d)
      self.rel_to_real[d] = r
      return r

  def is_ignored(self, f):
    for i in self.ignores:
      if fnmatch.fnmatch(f, i):
        return True
    return False

  def listdir(self, d):
    """Lists contents of a dir, but only using its realpath."""
    if d in self.dirs:
      de = self.dirs[d]
      if os.stat(d).st_mtime == de.st_mtime:
        return de.ents
      else:
        logging.info("directory %s changed", d)
        del self.dirs[d]
    st_mtime = os.stat(d).st_mtime
    try:
      ents = os.listdir(d)
    except OSError:
      ents = []

    ents = [e for e in ents if not self.is_ignored(e)]
    de = _DirEnt(st_mtime, ents)
    self.dirs[d] = de
    return de.ents

class _DBSync(object):
  def __init__(self, dirs, dir_cache):
    self.dir_cache = dir_cache
    self.dirs = dirs
    self.dir_cache.reset_realpath_cache()    
    self.files = set()
    self.pending = collections.deque()

    self.visited = set()

    # enqueue start points in reverse because the whole search is DFS
    reverse_dirs = list(dirs)
    reverse_dirs.reverse()
    for d in reverse_dirs:
      self.enqueue_dir(d)

  def step(self):
    d = self.pending.popleft()
    ents = [self.dir_cache.realpath(os.path.join(d, ent)) for ent in self.dir_cache.listdir(d)]
    for ent in ents:
      if os.path.isdir(ent):
        self.enqueue_dir(ent)
      else:
        self.files.add(ent)
    
  def run(self):
    while len(self.pending):
      self.step()

  def enqueue_dir(self, d):
    dr = self.dir_cache.realpath(d)
    if dr in self.visited:
      return
    self.visited.add(dr)
    self.pending.appendleft(dr)

