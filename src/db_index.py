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
import matchers

from dyn_object import DynObject

global slave

def SlaveInit(matcher_name, files_by_basename):
  global slave
  slave = matchers.matchers()[matcher_name](files_by_basename)

def SlaveSearchBasenames(query, max_hits):
  assert slave
  return slave.search_basenames(query, max_hits)

def SlaveSearchFilesInDirectoriesEndingWith(query, max_hits):
  assert slave
  return slave.search_files_in_directories_ending_with(query, max_hits)

def _get_num_cpus():
   """
   Detects the number of CPUs on a system. Cribbed from 
   http://codeliberates.blogspot.com/2008/05/detecting-cpuscores-in-python.html
   """
   # Linux, Unix and MacOS:
   if hasattr(os, "sysconf"):
     if os.sysconf_names.has_key("SC_NPROCESSORS_ONLN"):
       # Linux & Unix:
       ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
       if isinstance(ncpus, int) and ncpus > 0:
         return ncpus
       else: # OSX:
         return int(os.popen2("sysctl -n hw.ncpu")[1].read())
   # Windows:
   if os.environ.has_key("NUMBER_OF_PROCESSORS"):
     ncpus = int(os.environ["NUMBER_OF_PROCESSORS"]);
     if ncpus > 0:
       return ncpus
   return 1 # Default

class LocalPool(object):
  """
  Class that looks like a multiprocessing.Pool but executes locally.
  Used both to disable multiprocessing behavior without code changes AND
  to process a chunk locally while waiting on a subprocess for its results.
  """
  def __init__(self, n):
    assert n == 1

  def apply(self, fn, args=[]):
    return fn(*args)

  def apply_async(self, fn, args=[]):
    class Result(object):
      def get(self):
        return fn(*args)
    return Result()

class DBIndex(object):
  def __init__(self, indexer,matcher_name=None):
    if not matcher_name:
      matcher_name = matchers.default_matcher()
    if matcher_name not in matchers.matchers():
      raise Exception("Unrecognized matcher name")
    N = min(_get_num_cpus(), 4) # test for scaling beyond 4
    self.num_files_indexed = 0
    def makeChunks(items, N):
      base = 0
      chunksize = len(indexer.files_by_basename) / N
      if chunksize == 0:
        chunksize = 1
      chunks = []
      for i in range(N):
        chunk = dict()
        for j in items[base:base+chunksize]:
          self.num_files_indexed += len(j[1])
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
      pool.apply(SlaveInit, (matcher_name, chunk))

  @property
  def status(self):
    return "%i files indexed; %i-threaded searches" % (self.num_files_indexed, len(self.pools))

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
      for i in range(len(self.pools)):
        pool = self.pools[i]
        result_handles.append(pool.apply_async(SlaveSearchBasenames, (basepart, max_chunk_hits)))
      for h in result_handles:
        (subhits, subtruncated) = h.get()
        truncated |= subtruncated
        hits.extend(subhits)
    else:
      if len(dirpart):
        result_handles = []
        for i in range(len(self.pools)):
          pool = self.pools[i]
          result_handles.append(pool.apply_async(SlaveSearchFilesInDirectoriesEndingWith, (dirpart, max_chunk_hits)))
        for h in result_handles:
          (subhits, subtruncated) = h.get()
          truncated |= subtruncated
          hits.extend(subhits)
      else:
        hits = []

    if dirpart:
      reshits = []
      for hit in hits:
        dirname = os.path.dirname(hit[0])
        if dirname.endswith(dirpart):
          reshits.append(hit)
      hits = reshits

    # sort by rank
    hits.sort(lambda x,y: -cmp(x[1],y[1]))

    res = DynObject()
    res.hits = [c[0] for c in hits]
    res.ranks = [c[1] for c in hits]
    res.truncated = truncated
    return res
    
