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
    self.files_by_basename = files_by_basename
    self.basenames_unsplit = ("\n" + "\n".join(self.files_by_basename.keys()) + "\n").encode('utf8')
    assert type(self.basenames_unsplit) == str

  def get_filter(self, query):
    tmp = []
    for i in range(len(query)):
      tmp.append(re.escape(query[i]))
    flt = "\n.*%s.*\n" % '.*'.join(tmp)
    return flt

  def search_basenames(self, query, max_hits):
    # fuzzy match expression
    lower_query = query.lower()

    flt = self.get_filter(lower_query)
    regex = re.compile(flt)
    hits = dict()
    truncated = False
    base = 0
    ranker = Ranker()
    while True:
      m = regex.search(self.basenames_unsplit, base)
      if m:
        hit = m.group(0)[1:-1]
        rank = ranker.rank(query, hit)
        hits[hit] = rank
        base = m.end() - 1
        if len(hits) > max_hits:
          truncated = True
          break
      else:
        break
    return (hits, truncated)
