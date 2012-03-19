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
import query
from query import Query
from query_result import QueryResult

def make_result(hits):
  res = QueryResult()
  for h in hits:
    res.filenames.append(h)
    res.ranks.append(10)
  return res

class QueryTest(unittest.TestCase):
  def test_cons(self):
    Query("a")
    Query("a", 10)
    Query("a", 10, True)
    Query("a", 10, True, "blahblah")
    Query("a", 10, True, "blahblah", ["bar"])
  
  def test_to_and_from_dict(self):
    x = Query("a", 10, True, "blahblah", ["bar"])
    y = x.as_dict()
    z = Query.from_dict(y)

    self.assertEquals(x.text, z.text)
    self.assertEquals(x.max_hits, z.max_hits)
    self.assertEquals(x.exact_match, z.exact_match)
    self.assertEquals(x.current_filename, z.current_filename)
    self.assertEquals(x.open_filenames, z.open_filenames)

  def test_is_exact_match_1(self):
    self.assertTrue(query._is_exact_match("a.txt", "a.txt"))
    self.assertTrue(query._is_exact_match("b/a.txt", "b/a.txt"))

    self.assertTrue(query._is_exact_match("a.txt", "a/b/a.txt"))
    self.assertTrue(query._is_exact_match("abcd.txt", "a/b/abcd.txt"))
    self.assertFalse(query._is_exact_match("a.txt", "a/b/ba.txt"))

    self.assertFalse(query._is_exact_match("a/b.txt", "a/b/b.txt"))
    self.assertTrue(query._is_exact_match("a/b.txt", "a/a/b.txt"))

    self.assertFalse(query._is_exact_match("a/b.txt", "ba/b.txt"))

    self.assertFalse(query._is_exact_match("a/bcd.txt", "b/bcd.txt"))

  def test_filter_result_for_exact_matches(self):
    res = make_result(["a/bcd.txt", "b/bcd.txt"])

    exact_res = Query("bcd.txt").filter_result_for_exact_matches(res)
    self.assertEquals(len(exact_res.ranks), len(exact_res.filenames))
    self.assertEquals(2, len(exact_res.filenames))
    self.assertEquals(["a/bcd.txt", "b/bcd.txt"], exact_res.filenames)

    exact_res = Query("b/bcd.txt").filter_result_for_exact_matches(res)
    self.assertEquals(len(exact_res.ranks), len(exact_res.filenames))
    self.assertEquals(1, len(exact_res.filenames))
    self.assertEquals(["b/bcd.txt"], exact_res.filenames)

    exact_res = Query("x/bcd.txt").filter_result_for_exact_matches(res)
    self.assertEquals(len(exact_res.ranks), len(exact_res.filenames))
    self.assertEquals(0, len(exact_res.filenames))
    self.assertEquals([], exact_res.filenames)

  def test_rank_sort_and_adjustment_puts_suffixes_into_predictable_order(self):
    # render_widget.cpp should be get re-ranked higher than render_widget.h
    in_res = QueryResult(hits=[("render_widget.h", 10),
                               ("render_widget.cpp", 10)])
    res = Query("rw").apply_global_rank_adjustment(in_res)
    self.assertEquals(["render_widget.cpp",
                       "render_widget.h",], res.filenames)

    # render_widget.cpp should stay ranked higher than render_widget.h
    in_res = QueryResult(hits=[("render_widget.cpp", 10),
                              ("render_widget.h", 10)])
    res = Query("rw").apply_global_rank_adjustment(in_res)
    self.assertEquals(["render_widget.cpp",
                       "render_widget.h"], res.filenames)

    # but if the ranks mismatch, dont reorder
    in_res = QueryResult(hits=[("render_widget.cpp", 10),
                              ("render_widget.h", 12)])
    res = Query("rw").apply_global_rank_adjustment(in_res)
    self.assertEquals(["render_widget.h",
                       "render_widget.cpp"], res.filenames)

  def test_rank_sort_and_adjustment_puts_directories_into_predictable_order(self):
    # and if d if the ranks mismatch, dont reorder
    in_res = QueryResult(hits=[("b/render_widget.cpp", 10),
                               ("a/render_widget.cpp", 10)])
    res = Query("rw").apply_global_rank_adjustment(in_res)
    self.assertEquals(["a/render_widget.cpp",
                       "b/render_widget.cpp"], res.filenames)


