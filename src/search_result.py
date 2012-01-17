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

class SearchResult(object):
  def __init__(self, hits=None, ranks=None, items=None, truncated=False):
    if hits and ranks:
      self.hits = hits
      self.ranks = ranks
    elif items:
      self.hits = [x[0] for x in items]
      self.ranks = [x[1] for x in items]
    elif not hits and not ranks:
      self.hits = []
      self.ranks = []
    else:
      raise Exception("Unexpected")
    self.truncated = truncated

  def as_dict(self):
    return {"hits": self.hits,
            "ranks": self.ranks,
            "truncated": self.truncated}

  @staticmethod
  def from_dict(d):
    r = SearchResult()
    r.hits = d["hits"]
    r.ranks = d["ranks"]
    r.truncated = d["truncated"]
    return r

  def _is_exact_match(self, query, hit):
    # Endswith is a quick way to discard most non-exact matches.
    # e.g. a/b.txt matched by b.txt simply ending with b.txt
    if not hit.endswith(query):
      return False

    # This basic rule leaves the false positive:
    #    ba/b.txt  as exact for b.txt
    # so eliminate that as well by enforcing that the
    # match covers the full string or is immediatley to the right
    # of a separator.
    first_idx = hit.rfind(query)
    if first_idx == 0:
      return True
    if hit[first_idx - 1] == os.sep:
      return True
    return False

  def query_for_exact_matches(self, query):
    """
    Returns a new SearchResult object containing only hits that exactly
    match the provided query.
    """
    
    res = SearchResult()
    res.truncated = self.truncated

    for hit,rank in self.items():
      if self._is_exact_match(query, hit):
        res.hits.append(hit)
        res.ranks.append(rank)
    return res

  def is_empty(self):
    return len(self.hits) == 0

  def items(self):
    for i in range(len(self.hits)):
      yield (self.hits[i], self.ranks[i])

  def apply_global_rank_adjustment(self):
    def hit_cmp(x,y):
      # compare on the rank
      i = -cmp(x[1],y[1])
      if i != 0:
        return i
      # if the ranks agree, compare on the filename,
      # first by basename, then by fullname
      x_base = os.path.basename(x[0])
      y_base = os.path.basename(y[0])
      j = cmp(x_base, y_base)
      if j != 0:
        return j
      return cmp(x[0], y[0])

    items = list(self.items())
    items.sort(hit_cmp)
    self.hits = [x[0] for x in items]
    self.ranks = [x[1] for x in items]
