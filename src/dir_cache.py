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
import os
import fnmatch

class DirEnt(object):
  def __init__(self, st_mtime, ents):
    self.st_mtime = st_mtime
    self.ents = ents

class DirCache(object):
  def __init__(self):
    self.dirs = dict()
    self.rel_to_real = dict()
    self.ignores = []

  def set_ignores(self, ignores):
    if self.ignores != ignores:
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
    try:
      st = os.stat(d)
      st_mtime = st.st_mtime
      ents = os.listdir(d)
    except OSError:
      ents = []
      st_mtime = 0

    ents = [e for e in ents if not self.is_ignored(e)]
    de = DirEnt(st_mtime, ents)
    self.dirs[d] = de
    return de.ents

