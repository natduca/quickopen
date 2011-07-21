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

def matchers():
  return {
    "FuzFn": FuzzyFnMatcher,
    "FuzRe2": FuzzyRe2Matcher
  }

class FuzzyRe2Matcher(object):
  def __init__(self, files_by_basename, case_sensitive):
    self.case_sensitive = case_sensitive
    if case_sensitive:
      self.files_by_basename = files_by_basename
      files = self.files_by_basename.keys()
      files.sort()
      self.basenames_unsplit = ("\n" + "\n".join(files) + "\n").encode('utf8')
    else:
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

  def search(self, q, max_hits):
    if not self.case_sensitive:
      q = q.lower()
    # fuzzy match expression
    escaped_q = re.escape(q)
    tmp = []
    for i in range(len(escaped_q)):
      tmp.append(escaped_q[i])
    flt = "\n.*%s.*\n" % '.*'.join(tmp)
    regex = re.compile(flt)
    
    hits = []
    truncated = False
    base = 0
    while True:
      m = regex.search(self.basenames_unsplit, base)
      if m:
        hit = m.group(0)[1:-1]
        hits.extend(self.files_by_basename[hit])
        base = m.end() - 1
        if len(hits) > max_hits:
          truncated = True
          break
      else:
        break
    return (hits, truncated)

class FuzzyFnMatcher(object):
  def __init__(self, files_by_basename, case_sensitive):
    self.case_sensitive = case_sensitive
    self.files_by_basename = []
    self.files = []
    self.files_associated_with_basename = []
    for basename,files_with_basename in files_by_basename.items():
      idx_of_first_file = len(self.files)
      if case_sensitive:
        self.files_by_basename.append(basename)
      else:
        self.files_by_basename.append(basename.lower())
      self.files_associated_with_basename.append(idx_of_first_file)
      self.files_associated_with_basename.append(len(files_with_basename))
      self.files.extend(files_with_basename)

  def search(self, query, max_hits):
    if not self.case_sensitive:
      query = query.lower()
    tmp = ['*']
    for i in range(len(query)):
      tmp.append(query[i])
    tmp.append('*')
    flt = '*'.join(tmp)
    
    truncated = False
    hits = []
    for i in range(len(self.files_by_basename)):
      x = self.files_by_basename[i]
      if fnmatch.fnmatch(x, flt):
        lo = self.files_associated_with_basename[2*i]
        n = self.files_associated_with_basename[2*i+1]
        hits.extend(self.files[lo:lo+n])
        if len(hits) > max_hits:
          truncated = True
          break
    return (hits, truncated)

