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

def matchers():
  return {
    "FuzFn": FuzzyFnMatcher,
    "FuzRe2": FuzzyRe2Matcher,
#    "FuzRe2PreFB": FuzzyRe2PreFBMatcher
  }

def default_matcher():
  return "FuzRe2"

class FuzzyFnMatcher(object):
  def __init__(self, files_by_basename):
    self.files_by_basename = []
    self.files = []
    self.files_associated_with_basename = []
    for basename,files_with_basename in files_by_basename.items():
      idx_of_first_file = len(self.files)
      self.files_by_basename.append(basename.lower())
      self.files_associated_with_basename.append(idx_of_first_file)
      self.files_associated_with_basename.append(len(files_with_basename))
      self.files.extend(files_with_basename)

  def get_filter(self, query, lower_query):
    tmp = ['*']
    for i in range(len(lower_query)):
      tmp.append(lower_query[i])
    tmp.append('*')
    flt = '*'.join(tmp)
    return flt

  def search(self, query, max_hits):
    lower_query = query.lower()
    flt = self.get_filter(query, lower_query)
    
    truncated = False
    hits = []
    ranker = Ranker()
    for i in range(len(self.files_by_basename)):
      x = self.files_by_basename[i]
      if fnmatch.fnmatch(x, flt):
        rank = ranker.rank(query, x)
        lo = self.files_associated_with_basename[2*i]
        n = self.files_associated_with_basename[2*i+1]
        hits.extend([(p,rank) for p in self.files[lo:lo+n]])
        if len(hits) > max_hits:
          truncated = True
          break
    return (hits, truncated)


class OneBigStringRegexpMatcher(object):
  def __init__(self, files_by_basename):
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

  def search(self, query, max_hits):
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

class FuzzyRe2Matcher(OneBigStringRegexpMatcher):
  def get_filter(self, query, lower_query):
    tmp = []
    for i in range(len(query)):
      tmp.append(re.escape(lower_query[i]))
    flt = "\n.*%s.*\n" % '.*'.join(tmp)
    return flt

class FuzzyRe2PreFBMatcher(FuzzyRe2Matcher):
  def __init__(self, files_by_basename):
    self.fuzzy = FuzzyRe2Matcher(files_by_basename)

  def get_filter(query, lower_query):
    if len(query) >= 6:
      return "\n.*%s.*\n" % escaped_q
    else:
      return FuzzyFnMatcher.get_filter(query, lower_query)

