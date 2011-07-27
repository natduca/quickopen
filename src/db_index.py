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
import multiprocessing
import matcher

from dyn_object import DynObject

global slave

def SlaveInit(files_by_basename):
  global slave
  slave = matcher.Matcher(files_by_basename)

def SlaveSearchBasenames(query, max_hits):
  assert slave
  return slave.search_basenames(query, max_hits)

class LocalPool(object):
  """
  Class that looks like a multiprocessing.Pool but executes locally.
  Used both to disable multiprocessing behavior without code changes AND
  to process a chunk locally while waiting on a subprocess for its results.
  """
  def __init__(self, n):
    assert n == 1

  def apply(self, fn, args=()):
    return fn(*args)

  def apply_async(self, fn, args=()):
    class Result(object):
      def get(self):
        return fn(*args)
    return Result()

class DBIndex(object):
  def __init__(self, indexer, threaded = True):
    self.files = []
    self.files_by_lower_basename = dict()
    for basename,files_with_basename in indexer.files_by_basename.items():
      lower_basename = basename.lower()
      if lower_basename in self.files_by_lower_basename:
        self.files_by_lower_basename[lower_basename].extend(files_with_basename)
      else:
        self.files_by_lower_basename[lower_basename] = files_with_basename
      self.files.extend(files_with_basename)

    if threaded:
      N = min(multiprocessing.cpu_count(), 4) # test for scaling beyond 4
    else:
      N = 1

    def makeChunks(items, N):
      base = 0
      chunksize = len(items) / N
      if chunksize == 0:
        chunksize = 1
      chunks = []
      for i in range(N):
        chunk = dict()
        for j in items[base:base+chunksize]:
          chunk[j[0]] = j[1]
        base += chunksize
        chunks.append(chunk)
      return chunks
    chunks = makeChunks(list(indexer.files_by_basename.items()), N)

    self.pools = [LocalPool(1)]
    self.pools.extend([multiprocessing.Pool(1) for x in range(len(chunks)-1)])
    for i in range(len(self.pools)):
      chunk = chunks[i]
      pool = self.pools[i]
      pool.apply(SlaveInit, (chunk,))

  @property
  def status(self):
    return "%i files indexed; %i-threaded searches" % (len(self.files), len(self.pools))

  def close(self):
    self.pool.close()
    try:
      self.pool.join()
    except:
      self.pool.terminate()

  def search(self, query, max_hits = 100):
    slashIdx = query.rfind('/')
    if slashIdx != -1:
      dirpart = query[:slashIdx]
      basepart = query[slashIdx+1:]
    else:
      dirpart = None
      basepart = query

    hits = []
    truncated = False
    max_chunk_hits = max(1, max_hits / len(self.pools))
    if len(basepart):
      result_handles = []
      base_hits = dict()
      for i in range(len(self.pools)):
        pool = self.pools[i]
        result_handles.append(pool.apply_async(SlaveSearchBasenames, (basepart, max_chunk_hits)))
      for h in result_handles:
        (subhits, subtruncated) = h.get()
        truncated |= subtruncated
        for hit,rank in subhits.items():
          if hit in base_hits:
            base_hits[hit] = max(base_hits[hit],rank)
          else:
            base_hits[hit] = rank
      for hit,rank in base_hits.items():
        files = self.files_by_lower_basename[hit]
        for f in files:
          hits.append((f,rank))
    else:
      if len(dirpart):
        hits.extend([(f, 1) for f in self.files])
      else:
        hits = []

    if dirpart:
      reshits = []
      lower_dirpart = dirpart.lower()
      for hit in hits:
        dirname = os.path.dirname(hit[0])
        if dirname.endswith(lower_dirpart):
          reshits.append(hit)
      hits = reshits

    # sort by rank
    hits.sort(lambda x,y: -cmp(x[1],y[1]))

    res = DynObject()
    res.hits = [c[0] for c in hits]
    res.ranks = [c[1] for c in hits]
    res.truncated = truncated
    return res
    
