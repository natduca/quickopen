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

def ShardInit(basenames):
  global slave
  slave = db_index_shard.DBIndexShard(basenames)

def ShardSearchBasenames(basename_query):
  assert slave
  global slave_searchcount
  ret = slave.search_basenames(basename_query)
  slave_searchcount += 1
  if trace_is_enabled() and slave_searchcount % 10 == 0:
    trace_flush()
  return ret

class DBShardManager(object):
  """
  The DBShardManager takes a complete list of basenames in the database and manages the sharding
  of those basenames using the multiprocessing module.
  """
  def __init__(self, indexer):
    self.dirs = indexer.dirs
    self.files = []
    self.files_by_lower_basename = dict()
    for basename,files_with_basename in indexer.files_by_basename.items():
      lower_basename = basename.lower()
      if lower_basename in self.files_by_lower_basename:
        self.files_by_lower_basename[lower_basename].extend(files_with_basename)
      else:
        self.files_by_lower_basename[lower_basename] = files_with_basename
      self.files.extend(files_with_basename)

    N = min(multiprocessing.cpu_count(), 4) # Arbitrary limit to 4-threads.

    chunks = self._make_chunks(list(indexer.files_by_basename.keys()), N)

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
      chunk = items[base:base+chunksize]
      base += chunksize
      chunks.append(chunk)
    # Items may not have evenly divided by N.
    chunks[0].extend(items[base:])
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
    # Actually "delete" the shards. Some multiprocessing.Pool implementations
    # dont clean up their fd resources.
    del self.shards

  def search_basenames(self, basename_query):
    """
    Searches all controlled index shards for basenames matching the query.

    Returns (hits, truncated) where:
       hits is an array of basenames that matched.
       truncated is a bool indicated whether not all possible matches were found.
    """
    shard_result_handles = []
    # Run the search in parallel across the shards.
    trace_begin("issue_search")
    for i in range(len(self.shards)):
      shard = self.shards[i]
      shard_result_handles.append(shard.apply_async(ShardSearchBasenames, (basename_query,)))
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
