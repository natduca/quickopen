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
import re
import multiprocessing
import random

from dyn_object import DynObject

def matchers():
  return {
    "FuzFn": FuzzyFnMatcher,
    "FuzRe2": FuzzyRe2Matcher
  }

class FuzzyRe2Matcher(object):
  def __init__(self, files_by_basename, case_sensitive):
    if case_sensitive:
      self.files_by_basename = files_by_basename
      files = self.files_by_basename.keys()
      files.sort()
      self.basenames_unsplit = ("\n" + "\n".join(files) + "\n").encode('utf8')
    else:
      self.files_by_basename = {}
      basenames = files_by_basename.keys()
      basenames.sort()
      for bn in basenames:
        lbn = bn.lower()
        if lbn not in self.files_by_basename:
          self.files_by_basename[lbn] = []
        self.files_by_basename[lbn].extend(files_by_basename[bn])
      self.basenames_unsplit = ("\n" + "\n".join(self.files_by_basename.keys()) + "\n").encode('utf8')
    assert type(self.basenames_unsplit) == str

  def search(self, q, max_hits):
    # fuzzy match expression
    escaped_q = re.escape(q)
    tmp = []
    for i in range(len(escaped_q)):
      tmp.append(escaped_q[i])
    flt = "\n.*%s.*\n" % '.*'.join(tmp)
    regex = re.compile(flt)
    
    hits = []
    truncated = False
    base = 0
    while True:
      m = regex.search(self.basenames_unsplit, base)
      if m:
        hit = m.group(0)[1:-1]
        hits.extend(self.files_by_basename[hit])
        base = m.end() - 1
        if len(hits) > max_hits:
          truncated = True
          break
      else:
        break
    return (hits, truncated)

class FuzzyFnMatcher(object):
  def __init__(self, files_by_basename, case_sensitive):
    self.files_by_basename = []
    self.files = []
    self.files_associated_with_basename = []
    for basename,files_with_basename in files_by_basename.items():
      idx_of_first_file = len(self.files)
      if case_sensitive:
        self.files_by_basename.append(basename)
      else:
        self.files_by_basename.append(basename.lower())
      self.files_associated_with_basename.append(idx_of_first_file)
      self.files_associated_with_basename.append(len(files_with_basename))
      self.files.extend(files_with_basename)

  def search(self, query, max_hits):
    tmp = ['*']
    for i in range(len(query)):
      tmp.append(query[i])
    tmp.append('*')
    flt = '*'.join(tmp)
    
    truncated = False
    hits = []
    for i in range(len(self.files_by_basename)):
      x = self.files_by_basename[i]
      if fnmatch.fnmatch(x, flt):
        lo = self.files_associated_with_basename[2*i]
        n = self.files_associated_with_basename[2*i+1]
        hits.extend(self.files[lo:lo+n])
        if len(hits) > max_hits:
          truncated = True
          break
    return (hits, truncated)

global slave

def SlaveInit(matcher_name, files_by_basename, case_sensitive):
  global slave
  slave = matchers()[matcher_name](files_by_basename, case_sensitive)

def SlaveMSearch(query, max_hits):
  assert slave
  return slave.search( query, max_hits)

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
  def __init__(self, indexer,matcher_name='FuzRe2'):
    case_sensitive = True
    if matcher_name not in matchers():
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
      pool.apply(SlaveInit, (matcher_name, chunk, case_sensitive))

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
    if len(basepart):
      result_handles = []
      max_chunk_hits = max(1, max_hits / len(self.pools))
      for i in range(len(self.pools)):
        pool = self.pools[i]
        result_handles.append(pool.apply_async(SlaveMSearch, (basepart, max_chunk_hits)))
      for h in result_handles:
        (subhits, subtruncated) = h.get()
        truncated |= subtruncated
        hits.extend(subhits)
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
    
