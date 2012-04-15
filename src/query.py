# Copyright 2012 Google Inc.
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
import copy
import fixed_size_dict
import os
import sys
import time

from basename_ranker import BasenameRanker
from query_result import QueryResult
from trace_event import *

def _is_exact_match(query_text, hit):
  # Endswith is a quick way to discard most non-exact matches.
  # e.g. a/b.txt matched by b.txt simply ending with b.txt
  if not hit.endswith(query_text):
    return False

  # This basic rule leaves the false positive:
  #    ba/b.txt  as exact for b.txt
  # so eliminate that as well by enforcing that the
  # match covers the full string or is immediatley to the right
  # of a separator.
  first_idx = hit.rfind(query_text)
  if first_idx == 0:
    return True
  if hit[first_idx - 1] == os.sep:
    return True
  return False

class DirPriority(object):
  def __init__(self, dir, priority):
    self.dir = dir
    self.priority = priority

def _apply_global_rank_adjustment(base_result, indexed_dirs, query):
  all_open_filenames = []
  if query.current_filename:
    all_open_filenames.append(query.current_filename)
  all_open_filenames.extend(query.open_filenames)

  # The active_dir_orders goes from a directory prefix to an order
  # value.  We use this to break ties when the same basename crops up in two
  # places: the basename that is in the most recently active directory wins.
  #
  # This is built as a dict, but then converted to a flat list because we iterate it
  # during execution.
  inactive_dirs = set(indexed_dirs)
  active_dir_orders = {}
  for open_filename in all_open_filenames:
    for d in indexed_dirs:
      if open_filename.startswith(d):
        if d not in active_dir_orders:
          active_dir_orders[d] = len(active_dir_orders)
          inactive_dirs.remove(d)
  inactive_dirs = list(inactive_dirs)
  inactive_dirs.sort()
  for i in inactive_dirs:
    active_dir_orders[i] = len(active_dir_orders)
  active_dir_orders = [(x,y) for x,y in active_dir_orders.items()]

  def get_order(f):
    for d,order in active_dir_orders:
      if f.startswith(d):
        return order
    return sys.maxint

  def hit_cmp(x,y):
    # directory order trumps everything
    h = get_order(x[0]) - get_order(y[0])
    if h != 0:
      return h

    # compare on the rank
    j = -cmp(x[1],y[1])
    if j != 0:
      return j

    # if the ranks agree, compare on the filename,
    # first by basename, then by fullname
    x_base = os.path.basename(x[0])
    y_base = os.path.basename(y[0])
    j = cmp(x_base, y_base)
    if j != 0:
      return j

    # last resort is to compare full names
    return cmp(x[0], y[0])

  hits = list(base_result.hits)
  hits.sort(hit_cmp)
  new_hits = _rerank(hits)
  res = QueryResult(new_hits, base_result.truncated)
  res.debug_info = copy.deepcopy(base_result.debug_info)
  return res

def _rerank(hits):
  """
  Used to uniquefy ranks after sorting operations have been
  applied to position duplicate ranks.
  """
  if len(hits) == 0:
    return []
  # 12 12 12 11 10 -> 12 11.9 11.8 10.8 9.8
  # so adjust accordingly
  deltas = [1 for x in range(len(hits))]
  deltas[0] = 0
  for i in range(1, len(hits)):
    deltas[i] = hits[i][1] - hits[i-1][1]
  res = [hits[0]]
  for i in range(1, len(hits)):
    delta = deltas[i]
    if delta >= 0:
      delta = -0.1
    res.append((hits[i][0], res[i-1][1] + delta))
  return res

def _filter_result_for_exact_matches(query_text, base_result):
  """
  Returns a new QueryResult object containing only filenames that exactly
  match the provided query.
  """
  res = QueryResult()
  res.debug_info = copy.deepcopy(base_result.debug_info)
  res.truncated = base_result.truncated

  for hit,rank in base_result.hits:
    if _is_exact_match(query_text, hit):
      res.filenames.append(hit)
      res.ranks.append(rank)
  return res

def _is_dirmatch(lower_dirpart_query, filename):
  if lower_dirpart_query == '':
    return True

  dirname = os.path.dirname(filename)
  lower_dirname = dirname.lower()
  if lower_dirname.endswith(lower_dirpart_query):
    return True
  return False

class Query(object):
  """Encapsulates all the options to Quickopen search system."""

  def __init__(self, text, max_hits = 100, exact_match = False, current_filename = None, open_filenames = []):
    self.text = text
    self.max_hits = max_hits
    self.exact_match = exact_match
    self.current_filename = current_filename
    self.open_filenames = open_filenames
    self._dir_search_timeout = 0.2
    self.debug = False

  @staticmethod
  def from_kargs(args = [], kwargs = {}):
    """A wrapper for old mechanisms of implicitly constructing queries."""
    if len(args) == 1:
      if isinstance(args[0], Query):
        return args[0]
      else:
        return Query(*args, **kwargs)
    else:
      return Query(*args, **kwargs)

  @staticmethod
  def from_dict(d):
    q = Query(d["text"],
              d["max_hits"],
              d["exact_match"],
              d["current_filename"],
              d["open_filenames"])
    q.debug = d["debug"]
    return q

  def as_dict(self):
    return {
      "text": self.text,
      "max_hits": self.max_hits,
      "exact_match": self.exact_match,
      "current_filename": self.current_filename,
      "open_filenames": self.open_filenames,
      "debug": self.debug}


  @tracedmethod
  def execute(self, shard_manager, query_cache):
    """
    Searches the index given the provided query.

    args should be either a Query object, or arguments to the Query-object constructor.
    """
    if self.text == '':
      return QueryResult()

    assert self.max_hits >= 0

    res = query_cache.try_get(self)
    if not res:
      res_was_cache_hit = False
      ranked_results = self.execute_nocache(shard_manager, query_cache)
      ranked_and_truncated_results = ranked_results.get_copy_with_max_hits(self.max_hits)
      res = ranked_and_truncated_results
      query_cache.put(self, res)
    else:
      res_was_cache_hit = True

    if self.exact_match:
      final_res = _filter_result_for_exact_matches(self.text, res)
    else:
      final_res = _apply_global_rank_adjustment(res, shard_manager.dirs, self)

    if self.debug:
      final_res.debug_info.append({"res_was_cache_hit": res_was_cache_hit})
      final_res.debug_info.append({"initial_res": res.as_dict(),
                                    "dirs": shard_manager.dirs
                                    })
    return final_res

  def execute_nocache(self, shard_manager, query_cache):
    # What we'll actually return
    truncated = False

    slashIdx = self.text.rfind('/')
    if slashIdx != -1:
      dirpart_query = self.text[:slashIdx]
      basename_query = self.text[slashIdx+1:]
    else:
      dirpart_query = ''
      basename_query = self.text
    lower_dirpart_query = dirpart_query.lower()

    # Get the files
    files = []
    if len(basename_query):
      basename_hits, truncated = shard_manager.search_basenames(basename_query)
      for hit in basename_hits:
        hit_files = shard_manager.files_by_lower_basename[hit]
        for f in hit_files:
          if _is_dirmatch(lower_dirpart_query, f):
            files.append(f)
    else:
      i = 0
      start = time.time()
      timeout = start + self._dir_search_timeout
      for f in shard_manager.files:
        if _is_dirmatch(lower_dirpart_query, f):
          files.append(f)
        i += 1
        if i % 1000 == 0:
          if time.time() >= timeout:
            truncated = True
            break

    # Rank the results
    trace_begin("rank_results")
    hits = []
    basename_ranker = BasenameRanker()
    for f in files:
      basename = os.path.basename(f)
      rank = basename_ranker.rank_query(basename_query, basename)
      hits.append((f,rank))
    trace_end("rank_results")

    return QueryResult(hits=hits, truncated=truncated)
