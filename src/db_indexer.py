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
import time
import json

class MockIndexer(object):
  def __init__(self, filename):
    self.files_by_basename = json.load(open(filename))

class DBIndexer(object):
  def __init__(self, dirs, dir_cache):
    self.dir_cache = dir_cache
    self.dir_cache.reset_realpath_cache()

    self._basename_slots = dict()

    # variablse used both during indexing and once indexed
    self.files_by_basename = dict() # maps basename to list

    # variables used during indexing
    self.pending = collections.deque()
    self.visited = set()
    self.complete = False
    self.num_files_found = 0 # stats only

    # enqueue start points in reverse because the whole search is DFS
    reverse_dirs = list(dirs)
    reverse_dirs.reverse()
    for d in reverse_dirs:
      self.enqueue_dir(d)

  @property
  def progress(self):
    return "%i files found, %i dirs pending" % (self.num_files_found, len(self.pending))

  def index_a_bit_more(self):
    start = time.time()
    n = 0
    try:
      while time.time() - start < 0.25:
        i = 0
        while i < 10:
          self.step_one()
          i += 1
          n += 1
    except IndexError:
      pass
    if not len(self.pending):
      self.complete = True

  def enqueue_dir(self, d):
    dr = self.dir_cache.realpath(d)
    if dr in self.visited:
      return
    self.visited.add(dr)
    self.pending.appendleft(dr)

  def step_one(self):
    d = self.pending.popleft()
    for basename in self.dir_cache.listdir(d):
      path = self.dir_cache.realpath(os.path.join(d, basename))
      if os.path.isdir(path):
        self.enqueue_dir(path)
      else:
        if basename not in self.files_by_basename:
          self.files_by_basename[basename] = []
        self.files_by_basename[basename].append(path)
        self.num_files_found += 1
