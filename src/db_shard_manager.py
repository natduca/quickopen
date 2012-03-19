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
import multiprocessing

from local_pool import *
from trace_event import *

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

class DBShardManager(object):
  """
  The DBShardManager takes a complete list of basenames in the database and manages the sharding
  of those basenames using the multiprocessing module.
  """
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

  def search_basenames(self, basename_query, max_hits_hint):
    """
    Searches all controlled index shards for basenames matching the query.

    Returns (hits, truncated) where:
       hits is an array of basenames that matched.
       truncated is a bool indicated whether not all possible matches were found.

    Note: max_hits_hint does not control the amount of hits created. Its rather just a way to
    limit the work done per shard to a reasonable value. If you want an actual maximum result size,
    enforce that in an upper layer.
    """
    max_shard_hits_hint = max(10, max_hits_hint / len(self.shards))

    shard_result_handles = []
    # Run the search in parallel across the shards.
    trace_begin("issue_search")
    for i in range(len(self.shards)):
      shard = self.shards[i]
      shard_result_handles.append(shard.apply_async(ShardSearchBasenames, (basename_query, max_shard_hits_hint)))
    trace_end("issue_search")

    # union the results
    trace_begin("gather_results")
    base_hits = set()
    truncated = False
    for shard_result_handle in shard_result_handles:
      (shard_hits, shard_hits_truncated) = shard_result_handle.get()
      truncated |= shard_hits_truncated
      for hit in shard_hits:
        base_hits.add(hit)
    trace_end("gather_results")
    return list(base_hits), truncated
