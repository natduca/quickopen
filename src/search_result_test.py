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
import unittest
from search_result import SearchResult

class SearchResultTest(unittest.TestCase):
  def test_is_exact_match_1(self):
    res = SearchResult()
    self.assertTrue(res._is_exact_match("a.txt", "a.txt"))
    self.assertTrue(res._is_exact_match("b/a.txt", "b/a.txt"))

    self.assertTrue(res._is_exact_match("a.txt", "a/b/a.txt"))
    self.assertTrue(res._is_exact_match("abcd.txt", "a/b/abcd.txt"))
    self.assertFalse(res._is_exact_match("a.txt", "a/b/ba.txt"))

    self.assertFalse(res._is_exact_match("a/b.txt", "a/b/b.txt"))
    self.assertTrue(res._is_exact_match("a/b.txt", "a/a/b.txt"))

    self.assertFalse(res._is_exact_match("a/b.txt", "ba/b.txt"))

    self.assertFalse(res._is_exact_match("a/bcd.txt", "b/bcd.txt"))

  def make_result(self, hits):
    res = SearchResult()
    for h in hits:
      res.hits.append(h)
      res.ranks.append(10)
    return res

  def test_query_for_exact_matches(self):
    res = self.make_result(["a/bcd.txt", "b/bcd.txt"])

    exact_res = res.query_for_exact_matches("bcd.txt")
    self.assertEquals(len(exact_res.ranks), len(exact_res.hits))
    self.assertEquals(2, len(exact_res.hits))
    self.assertEquals(["a/bcd.txt", "b/bcd.txt"], exact_res.hits)

    exact_res = res.query_for_exact_matches("b/bcd.txt")
    self.assertEquals(len(exact_res.ranks), len(exact_res.hits))
    self.assertEquals(1, len(exact_res.hits))
    self.assertEquals(["b/bcd.txt"], exact_res.hits)

    exact_res = exact_res.query_for_exact_matches("x/bcd.txt")
    self.assertEquals(len(exact_res.ranks), len(exact_res.hits))
    self.assertEquals(0, len(exact_res.hits))
    self.assertEquals([], exact_res.hits)

  def test_rank_sort_and_adjustment_puts_suffixes_into_predictable_order(self):
    res = SearchResult()
    # render_widget.cpp should be get re-ranked higher than render_widget.h
    adj = res.sort_and_adjust_ranks_given_complete_hit_list([
        ("render_widget.h", 10),
        ("render_widget.cpp", 10),
        ])
    self.assertEquals([("render_widget.cpp", 10),
                       ("render_widget.h", 10)], adj)

    # render_widget.cpp should stay ranked higher than render_widget.h
    adj = res.sort_and_adjust_ranks_given_complete_hit_list([
        ("render_widget.cpp", 10),
        ("render_widget.h", 10),
        ])
    self.assertEquals([("render_widget.cpp", 10),
                       ("render_widget.h", 10)], adj)

    # but if the ranks mismatch, dont reorder
    adj = res.sort_and_adjust_ranks_given_complete_hit_list([
        ("render_widget.cpp", 10),
        ("render_widget.h", 12),
        ])
    self.assertEquals([("render_widget.h", 12),
                       ("render_widget.cpp", 10)], adj)

  def test_rank_sort_and_adjustment_puts_directories_into_predictable_order(self):
    res = SearchResult()

    # and if d if the ranks mismatch, dont reorder
    adj = res.sort_and_adjust_ranks_given_complete_hit_list([
        ("b/render_widget.cpp", 10),
        ("a/render_widget.cpp", 10),
        ])
    self.assertEquals([("a/render_widget.cpp", 10),
                       ("b/render_widget.cpp", 10)], adj)


