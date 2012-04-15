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

class QueryResult(object):
  def __init__(self, hits=None, truncated=False):
    if hits:
      self._filenames = [x[0] for x in hits]
      self._ranks = [x[1] for x in hits]
    else:
      self._filenames = []
      self._ranks = []
    self.truncated = truncated
    self.debug_info = []

  def as_dict(self):
    return {"hits": list(self.hits),
            "truncated": self.truncated,
            "debug_info": self.debug_info}

  @staticmethod
  def from_dict(d):
    r = QueryResult()
    r._filenames = [x[0] for x in d["hits"]]
    r._ranks = [x[1] for x in d["hits"]]
    r.truncated = d["truncated"]
    r.debug_info = d["debug_info"]
    return r

  def is_empty(self):
    return len(self.filenames) == 0

  @property
  def filenames(self):
    return self._filenames

  @property
  def ranks(self):
    return self._ranks

  @property
  def hits(self):
    for i in range(len(self.filenames)):
      yield (self.filenames[i], self.ranks[i])

  def get_copy_with_max_hits(self, max_hits):
    return QueryResult(hits=list(self.hits)[:max_hits], truncated=self.truncated)

  def rank_of(self, filename):
    for i in range(len(self.filenames)):
      if self.filenames[i] == filename:
        return self.ranks[i]
    raise Exception("%s not found" % filename)
