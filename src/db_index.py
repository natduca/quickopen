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
import db_index_shard
import fixed_size_dict
import multiprocessing
import os
from basename_ranker import BasenameRanker
from search_result import SearchResult
from trace_event import *

from local_pool import *

slave = None
slave_searchcount = 0

def ShardInit(files_by_basename):
  global slave
  slave = db_index_shard.DBIndexShard(files_by_basename)

def ShardSearchBasenames(query, max_hits):
  assert slave
  global slave_searchcount
  ret = slave.search_basenames(query, max_hits)
  slave_searchcount += 1
  if trace_is_enabled() and slave_searchcount % 10 == 0:
    trace_flush()
  return ret

class DBIndex(object):
  """
  The DBIndex takes a complete list of basenames in the database and manages the sharding
  of those basenames into DBIndexShards hosted using the multiprocessing module.
  """
  def __init__(self, indexer, threaded = True):
    self.query_cache = fixed_size_dict.FixedSizeDict(256)
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

    self._basename_ranker = BasenameRanker()
    chunks = self._make_chunks(list(indexer.files_by_basename.items()), N)

    self.shards = [LocalPool(1)]
    self.shards.extend([multiprocessing.Pool(1) for x in range(len(chunks)-1)])

    for i in range(len(self.shards)):
      chunk = chunks[i]
      shard = self.shards[i]
      shard.apply(ShardInit, (chunk,))

  def _make_chunks(self, items, N):
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
    # items may not have evenly divided by N
    for j in items[base:]:
        chunks[0][j[0]] = j[1]
    return chunks

  @property
  def status(self):
    return "%i files indexed; %i-threaded searches" % (len(self.files), len(self.shards))

  def close(self):
    for p in self.shards:
      p.close()
      try:
        p.join()
      except:
        p.terminate()

  @tracedmethod
  def search(self, query, max_hits = 100):
    qkey = query + "@%i" % max_hits
    assert len(query) > 0
    if qkey in self.query_cache:
      res = self.query_cache[qkey]
      return res

    res = self.search_nocache(query, max_hits)
    self.query_cache[qkey] = res
    return res

  def search_nocache(self, query, max_hits = 100):
    slashIdx = query.rfind('/')
    if slashIdx != -1:
      dirpart = query[:slashIdx]
      basename_query = query[slashIdx+1:]
    else:
      dirpart = None
      basename_query = query

    hits = []
    truncated = False

    # max_shard_hits does not control the amount of hits created. Its rather just a way to
    # limit the work done per shard to a reasonable value. The max_hits value is enforced
    # after all shard results have been computed.
    max_shard_hits = max(10, max_hits / len(self.shards))
    if len(basename_query):
      shard_result_handles = []
      # Run the search in parallel across the shards.
      trace_begin("issue_search")
      for i in range(len(self.shards)):
        shard = self.shards[i]
        shard_result_handles.append(shard.apply_async(ShardSearchBasenames, (basename_query, max_shard_hits)))
      trace_end("issue_search")

      # union the results
      trace_begin("gather_results")
      base_hits = set()
      for shard_result_handle in shard_result_handles:
        (shard_hits, shard_hits_truncated) = shard_result_handle.get()
        truncated |= shard_hits_truncated
        for hit in shard_hits:
          base_hits.add(hit)
      trace_end("gather_results")

      trace_begin("rank_results")
      for hit in base_hits:
        files = self.files_by_lower_basename[hit]
        for f in files:
          basename = os.path.basename(f)
          rank = self._basename_ranker.rank_query(basename_query, basename)
          hits.append((f,rank))
      trace_end("rank_results")
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
        lower_dirname = dirname.lower()
        if lower_dirname.endswith(lower_dirpart):
          reshits.append(hit)
      hits = reshits

    # do one final ranking on the total rank
    res = SearchResult(items=hits, truncated=truncated)
    res.apply_global_rank_adjustment()

    trimmed_res = SearchResult(items=list(res.items())[:max_hits], truncated=res.truncated)
    return trimmed_res

