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
      self.filenames = [x[0] for x in hits]
      self.ranks = [x[1] for x in hits]
    else:
      self.filenames = []
      self.ranks = []
    self.truncated = truncated

  def as_dict(self):
    return {"filenames": self.filenames,
            "ranks": self.ranks,
            "truncated": self.truncated}

  @staticmethod
  def from_dict(d):
    r = QueryResult()
    r.filenames = d["filenames"]
    r.ranks = d["ranks"]
    r.truncated = d["truncated"]
    return r

  def is_empty(self):
    return len(self.filenames) == 0

  def hits(self):
    for i in range(len(self.filenames)):
      yield (self.filenames[i], self.ranks[i])

  def set_hits(self, hits):
    self.filenames = [x[0] for x in hits]
    self.ranks = [x[1] for x in hits]

  def get_copy_with_max_hits(self, max_hits):
    return QueryResult(hits=list(self.hits())[:max_hits], truncated=self.truncated)
