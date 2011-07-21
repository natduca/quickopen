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
import ranker
import re

class Ranker(object):
  def rank(self, query, hit):
    return self.get_num_hits_on_word_starts(query, hit)

  def get_starts(self, word):
    if re.search('_', word):
      # underscore delimited
      words = re.split('_', word)
      if len(words[-1]) == 0:
        del words[-1]
    else:
      # case delimited
      words = re.split('[^A-Z](?=[A-Z])', word)
    base = 0
    res = []
    for w in words:
      res.append(base)
      base += len(w) + 1
    return res

  def get_num_hits_on_word_starts(self, query, orig_hit):
    starts = self.get_starts(orig_hit)
    if len(starts) == 0:
      return
    hit = orig_hit.lower()
    start_letters = [hit[i] for i in starts]

    # escape the query
    escaped_q = re.escape(query)
    # go xyz --> (.*)x(.*)y(.*)z(.*)
    tmp = ['(.*?)']
    for i in range(len(escaped_q)):
      tmp.append('(%s.*)' % escaped_q[i])
    flt = ''.join(tmp)
    m = re.match(flt, hit)
    assert m
    ngroups = len(tmp) - 1

    groups = m.groups()
    group_starts = [0]
    for i in range(1,len(groups)):
      group_starts.append(group_starts[i-1] + len(groups[i-1]))

    score = 0

    # you get one point for matching the first letter
    if len(groups[0]) == 0 and groups[1][0] == hit[starts[0]]:
      score += 1

    # you get one point for every matching letter that was a start letter
    for i in range(1, len(groups)):
      # look for start_letter to the left of group_start[i]
      # that matches groups[i][0]
      if len(groups[i]) == 0:
        continue
      letter_to_look_for = groups[i][0]
      leftmost_start_index = group_starts[i]
      for j in range(len(start_letters)):
        if starts[j] < leftmost_start_index:
          continue
        if start_letters[j] == letter_to_look_for:
          score += 1

    return score
