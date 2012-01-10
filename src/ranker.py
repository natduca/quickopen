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
import os
import math

class Ranker(object):
  def _is_wordstart(self, string, index):
    if index == 0:
      return True
    prev_char = string[index - 1]

    c = string[index]
    cprev = string[index - 1]
    if cprev == '_' or cprev == '.':
      return c != '_'

    if c.isupper() and not cprev.isupper():
      return True

    return False

  def get_num_words(self, word):
    n = 0
    for i in range(len(word)):
      if self._is_wordstart(word, i):
        n += 1
    return n

  def get_starts(self, word):
    res = []
    for i in range(len(word)):
      if self._is_wordstart(word, i):
        res.append(i)
    return res

  def get_start_letters(self, s):
    starts = self.get_starts(s)
    s_lower = s.lower()
    return [s_lower[i] for i in starts]

  def get_num_hits_on_word_starts_old(self, query, orig_hit, truncated = False):
    starts = self.get_starts(orig_hit)
    if len(starts) == 0:
      return 0
    hit = orig_hit.lower()
    start_letters = [hit[i] for i in starts]

    # escape the query
    lower_query = query.lower()
    # go xyz --> (.*)x(.*)y(.*)z(.*)
    tmp = ['(.*?)']
    for i in range(len(lower_query)):
      tmp.append('(%s.*)' % re.escape(lower_query[i]))
    flt = ''.join(tmp)
    m = re.match(flt, hit)
    if not m:
      if len(query) > 1:
        return  self.get_num_hits_on_word_starts(query[:-1],hit,True)
      return 0
    ngroups = len(tmp) - 1

    groups = m.groups()
    group_starts = [0]
    for i in range(1,len(groups)):
      group_starts.append(group_starts[i-1] + len(groups[i-1]))

    score = 0

    # you get one point for matching the first letter
    try:
      if len(groups[0]) == 0 and groups[1][0] == hit[starts[0]]:
        score += 1
    except:
      raise Exception("error while processing q=%s h=%s" % (query, hit))

    # you get one point for every matching letter that was a start letter
    hits = 0
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
          hits += 1

    # you get +1 if you match every letter in the word
    if hits == len(start_letters) == ngroups and not truncated:
      score += 1
    return score


  def rank(self, query, candidate, truncated = False):
    basic_rank, num_word_hits = self._get_basic_rank(query, candidate)

    rank = basic_rank

    # Give bonus for starting with the right letter, or for starting with the
    # right second letter.  We use the second letter because the latenc of
    # starting the open dialog sometimes causes the first letter to be dropped.
    #if len(query) >= 3 and len(candidate) >= len(query):
    #  if candidate[0] == query[0] or candidate[1] == query[0]:
    #    rank += 1

    # Give bonus for hitting all the words.
    if not truncated:
      max_num_word_hits = self.get_num_words(candidate)
      if max_num_word_hits > 2:
        percent_hit = float(num_word_hits) / max_num_word_hits
        rank += 4 * percent_hit # tune this constant

    # big points if you match the full string
    #candidatebase = os.path.splitext(candidate)[0]
    #querybase = os.path.splitext(query)[0]
    #if querybase == candidatebase:
    #  rank *= 2
    return math.floor(rank*10) / 10;

  def _get_basic_rank(self, query, candidate):
    memoized_results = {"": (0, 0)}
    return self._get_basic_rank_core(memoized_results, query.lower(), 0, candidate, candidate.lower())

  def _get_basic_rank_core(self, memoized_results, query, candidate_index, candidate, lower_candidate):
    """
    This function tries to find the best match of the given query to the candidate. For
    a given query xyz, it considers all possible order-preserving assignments of the leters .*x.*y.*z.* into candidate.

    For these configurations, it computes a rank based on whether the matched
    letter falls on the start of a word or not.

    The highest ranked option determines the basic rank.
    """
    if query in memoized_results:
      return memoized_results[query]

#    input_candidate_index = candidate_index
#    print "[%s] %30s" % ("%10s" % query, candidate[candidate_index:])

    # Find the best possible rank for this, memoizing results to keep
    # this from running forever.
    best_rank = 0
    for_best_frank__num_word_hits = 0
    while True:
      i = lower_candidate[candidate_index:].find(query[0])
      if i == -1:
        break
      i = i + candidate_index

      if self._is_wordstart(candidate, i):
        letter_rank = 2
        cur_num_word_hits = 1
      else:
        letter_rank = 1
        cur_num_word_hits = 0

      # consider all sub-interpretations...
      best_remainder_rank, remainder_num_word_hits = self._get_basic_rank_core(memoized_results, query[1:], i + 1, candidate, lower_candidate)

      # update best_rank
      rank = letter_rank + best_remainder_rank
      if rank > best_rank:
        best_rank = rank
        for_best_frank__num_word_hits = remainder_num_word_hits + cur_num_word_hits
      # advance to next candidate
      candidate_index = i + 1

    memoized_results[query] = (best_rank, for_best_frank__num_word_hits)
#    print "[%s] %30s -> %i" % ("%10s" % query, candidate[input_candidate_index:], best_rank)
    return best_rank, for_best_frank__num_word_hits
