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
import logging

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
      def fixpath(p):
        if p.find(os.path.sep) != -1:
          tmp = os.path.expanduser(p)
          return os.path.realpath(tmp)
        else:
          return p
      self.ignores = [fixpath(i) for i in ignores]

  def reset_realpath_cache(self):
    self.rel_to_real = dict()

  def realpath(self, d):
    if d in self.rel_to_real:
      return self.rel_to_real[d]
    else:
      r = os.path.realpath(d)
      self.rel_to_real[d] = r
      return r

  def is_ignored(self, basename, fullname):
    for i in self.ignores:
      if i.find(os.path.sep) != -1:
        if fnmatch.fnmatch(fullname, i):
          return True
      else:
        if fnmatch.fnmatch(basename, i):
          return True
    return False

  def listdir(self, d):
    """Lists contents of a dir, but only using its realpath."""
    if d in self.dirs:
      de = self.dirs[d]
      try:
        st_mtime = os.stat(d).st_mtime
      except OSError:
        st_mtime = 0
        del self.dirs[d]
        logging.debug("directory %s gone", d)
        return []

      if st_mtime == de.st_mtime:
        return de.ents
      else:
        logging.debug("directory %s changed", d)
        del self.dirs[d]
    try:
      st = os.stat(d)
      st_mtime = st.st_mtime
      ents = os.listdir(d)
    except OSError:
      return []

    ents = [e for e in ents if not self.is_ignored(e, os.path.join(d, e))]
    de = DirEnt(st_mtime, ents)
    self.dirs[d] = de
    return de.ents
