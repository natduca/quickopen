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

    self.files_by_lower_basename = dict()
    for basename,files_with_basename in files_by_basename.items():
      lower_basename = basename.lower()
      if lower_basename in self.files_by_lower_basename:
        self.files_by_lower_basename[lower_basename].extend(files_with_basename)
      else:
        self.files_by_lower_basename[lower_basename] = files_with_basename

    self.basenames_unsplit = ("\n" + "\n".join(self.files_by_basename.keys()) + "\n").encode('utf8')
    self.lower_basenames_unsplit = ("\n" + "\n".join(self.files_by_lower_basename.keys()) + "\n").encode('utf8')
    assert type(self.lower_basenames_unsplit) == str

  def search_basenames(self, query, max_hits):
    lower_query = query.lower()

    hits = dict()

    # word starts first
    self.add_all_matching( hits, query, self.get_camelcase_wordstart_filter(lower_query), max_hits )
    self.add_all_matching( hits, query, self.get_delimited_wordstart_filter(lower_query), max_hits )

    # add in superfuzzy matches
    self.add_all_matching( hits, query, self.get_superfuzzy_filter(lower_query), max_hits )

    return hits, len(hits) == max_hits

  def get_delimited_wordstart_filter(self, query):
    query = [re.escape(query[i]) for i in range(len(query))]
    # abc -> ^a.*_b.*_c
    # abc -> .*_a.*_b.*_c
    tmp = []
    tmp.append("(?:(?:%s)|(?:.*_%s))" % (query[0], query[0]))
    for i in range(1, len(query)):
      c = query[i]
      tmp.append("_%s" % query[i])
    flt = "\n%s.*\n" % '.*'.join(tmp)
    return (flt, False)

  def get_camelcase_wordstart_filter(self, query):
    query = query.upper()
    query = [re.escape(query[i]) for i in range(len(query))]
    # abc -> A.*B.*C
    #        .*[^A-Z]A.*
    tmp = []
    tmp.append("(?:(?:%s)|(?:.*[^A-Z\n]%s))" % (query[0], query[0]))
    for i in range(1, len(query)):
      tmp.append("[^A-Z\n]%s" % query[i])
    flt = "\n.*%s.*\n" % '.*'.join(tmp)
    return (flt, True)

  def get_superfuzzy_filter(self, query):
    tmp = []
    for i in range(len(query)):
      tmp.append(re.escape(query[i]))
    flt = "\n.*%s.*\n" % '.*'.join(tmp)
    return (flt, False)

  def add_all_matching(self, hits, query, flt_tuple, max_hits):
    """
    hits is the dictionary to put results in
    query is the query string originally entered by user, used by ranking
    flt_tuple is [filter_regex, case_sensitive_bool]
    max_hits is largest hits should grow before matching terminates.
    """
    flt, case_sensitive = flt_tuple

    regex = re.compile(flt)
    base = 0
    ranker = Ranker()
    if not case_sensitive:
      index = self.lower_basenames_unsplit
    else:
      index = self.basenames_unsplit
    while True:
      m = regex.search(index, base)
      if m:
        hit = m.group(0)[1:-1]
        if hit.find('\n') != -1:
          raise Exception("Somethign is messed up with flt=[%s] query=[%s] hit=[%s]" % (flt,query,hit))
        rank = ranker.rank(query, hit)
        if case_sensitive:
          hit = hit.lower()
        if hit in hits:
          hits[hit] = max(hits[hit],rank)
        else:
          hits[hit] = rank
        base = m.end() - 1
        if len(hits) > max_hits:
          truncated = True
          break
      else:
        break
