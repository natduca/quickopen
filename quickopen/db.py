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
import os
import re

class DB(object):
  def __init__(self, settings):
    self.settings = settings
    self.settings.register('dirs', list, [])
    self._dir_cache = _DirCache()
    self._dirty = True

  @property
  def dirs(self):
    return list(self.settings.dirs)

  def add_dir(self, dir):
    cur = list(self.settings.dirs)
    if dir in cur:
      return
    # commit change
    cur.append(dir)
    self.settings.dirs = cur
    self._set_dirty()

  def _set_dirty(self):
    self._dirty = True

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

    if self._dirty:
      self.sync()

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

  def reset_realpath_cache(self):
    self.rel_to_real = dict()

  def realpath(self, d):
    if d in self.rel_to_real:
      return self.rel_to_real[d]
    else:
      r = os.path.realpath(d)
      self.rel_to_real[d] = r
      return r

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
    ents = os.listdir(d)
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

