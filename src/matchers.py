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
import fnmatch
import re

from ranker import Ranker

class Matcher(object):
  def __init__(self, files_by_basename):
    self.files_by_basename = {}
    self.files = []
    basenames = files_by_basename.keys()
    basenames.sort()
    for bn in basenames:
      lbn = bn.lower()
      if lbn not in self.files_by_basename:
        self.files_by_basename[lbn] = []
      files = files_by_basename[bn]
      self.files_by_basename[lbn].extend(files)
      self.files.extend(files)
      self.basenames_unsplit = ("\n" + "\n".join(self.files_by_basename.keys()) + "\n").encode('utf8')
    assert type(self.basenames_unsplit) == str

  def get_filter(self, query, lower_query):
    tmp = []
    for i in range(len(query)):
      tmp.append(re.escape(lower_query[i]))
    flt = "\n.*%s.*\n" % '.*'.join(tmp)
    return flt

  def search_basenames(self, query, max_hits):
    # fuzzy match expression
    lower_query = query.lower()

    flt = self.get_filter(query, lower_query)
    regex = re.compile(flt)
    hits = []
    truncated = False
    base = 0
    ranker = Ranker()
    while True:
      m = regex.search(self.basenames_unsplit, base)
      if m:
        hit = m.group(0)[1:-1]
        rank = ranker.rank(query, hit)
        hits.extend([(h, rank) for h in self.files_by_basename[hit]])
        base = m.end() - 1
        if len(hits) > max_hits:
          truncated = True
          break
      else:
        break
    return (hits, truncated)
