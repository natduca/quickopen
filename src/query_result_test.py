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
from query_result import QueryResult

class QueryResultTest(unittest.TestCase):
  def test_is_exact_match_1(self):
    res = QueryResult()
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
    res = QueryResult()
    for h in hits:
      res.filenames.append(h)
      res.ranks.append(10)
    return res

  def test_query_for_exact_matches(self):
    res = self.make_result(["a/bcd.txt", "b/bcd.txt"])

    exact_res = res.query_for_exact_matches("bcd.txt")
    self.assertEquals(len(exact_res.ranks), len(exact_res.filenames))
    self.assertEquals(2, len(exact_res.filenames))
    self.assertEquals(["a/bcd.txt", "b/bcd.txt"], exact_res.filenames)

    exact_res = res.query_for_exact_matches("b/bcd.txt")
    self.assertEquals(len(exact_res.ranks), len(exact_res.filenames))
    self.assertEquals(1, len(exact_res.filenames))
    self.assertEquals(["b/bcd.txt"], exact_res.filenames)

    exact_res = exact_res.query_for_exact_matches("x/bcd.txt")
    self.assertEquals(len(exact_res.ranks), len(exact_res.filenames))
    self.assertEquals(0, len(exact_res.filenames))
    self.assertEquals([], exact_res.filenames)

  def test_rank_sort_and_adjustment_puts_suffixes_into_predictable_order(self):
    res = QueryResult(hits=[("render_widget.h", 10),
                              ("render_widget.cpp", 10)])
    # render_widget.cpp should be get re-ranked higher than render_widget.h
    res.apply_global_rank_adjustment()
    self.assertEquals(["render_widget.cpp",
                       "render_widget.h",], res.filenames)

    # render_widget.cpp should stay ranked higher than render_widget.h
    res = QueryResult(hits=[("render_widget.cpp", 10),
                              ("render_widget.h", 10)])

    res.apply_global_rank_adjustment()
    self.assertEquals(["render_widget.cpp",
                       "render_widget.h"], res.filenames)

    # but if the ranks mismatch, dont reorder
    res = QueryResult(hits=[("render_widget.cpp", 10),
                              ("render_widget.h", 12)])
    res.apply_global_rank_adjustment()
    self.assertEquals(["render_widget.h",
                       "render_widget.cpp"], res.filenames)

  def test_rank_sort_and_adjustment_puts_directories_into_predictable_order(self):
    res = QueryResult(hits=[("b/render_widget.cpp", 10),
                              ("a/render_widget.cpp", 10)])

    # and if d if the ranks mismatch, dont reorder
    res.apply_global_rank_adjustment()
    self.assertEquals(["a/render_widget.cpp",
                       "b/render_widget.cpp"], res.filenames)


