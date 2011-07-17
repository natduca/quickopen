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
import hashlib
import os
import re
import threading
import time

from dyn_object import DynObject
from event import Event

class DBIndex(object):
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

    # variables used once indexed
    self.files = []
    self.files_associated_with_basename = []


    # enqueue start points in reverse because the whole search is DFS
    reverse_dirs = list(dirs)
    reverse_dirs.reverse()
    for d in reverse_dirs:
      self.enqueue_dir(d)

  def index_a_bit_more(self):
    start = time.time()
    n = 0
    try:
      while time.time() - start < 0.15:
        i = 0
        while i < 10:
          self.step_one()
          i += 1
          n += 1
    except IndexError:
      self.commitResult()

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

  def commitResult(self):
    self.complete = True
    tmp = self.files_by_basename
    self.files_by_basename = [] # change to list    
    for basename,files_with_basename in tmp.items():
      idx_of_first_file = len(self.files)
      self.files_by_basename.append(basename)
      self.files_associated_with_basename.append(idx_of_first_file)
      self.files_associated_with_basename.append(len(files_with_basename))
      self.files.extend(files_with_basename)

  def search(self, query):
    slashIdx = query.rfind('/')
    if slashIdx != -1:
      dirpart = query[:slashIdx]
      basepart = query[slashIdx+1:]
    else:
      dirpart = None
      basepart = query

    # fuzz the basepart
    if 1:
      tmp = ['*']
      for i in range(len(basepart)):
        tmp.append(basepart[i])
      tmp.append('*')
      basepart = '*'.join(tmp)
    
    hits = []
    truncated = False
    if len(basepart):
      for i in range(len(self.files_by_basename)):
        x = self.files_by_basename[i]
        if fnmatch.fnmatch(x, basepart):
          lo = self.files_associated_with_basename[2*i]
          n = self.files_associated_with_basename[2*i+1]
          hits.extend(self.files[lo:lo+n])
          if len(hits) > 100:
            truncated = True
            break
    else:
      hits = self.files

    if dirpart:
      reshits = []
      for path in hits:
        dirname = os.path.dirname(path)
        if dirname.endswith(dirpart):
          reshits.append(path)
      hits = reshits
        
    res = DynObject()
    res.hits = hits
    res.truncated = truncated
    return res
