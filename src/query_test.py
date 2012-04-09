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
import os
import unittest
import query

from basename_ranker import BasenameRanker
from query import Query
from query_cache import QueryCache
from query_result import QueryResult

def make_result(hits):
  res = QueryResult()
  for h in hits:
    res.filenames.append(h)
    res.ranks.append(10)
  return res


class FakeDBShardManager(object):
  """
  A super-simple implementation of the DBShardManager interface for use
  in unit tests. Uses file.find(query_text) != -1 as a match.
  """
  def __init__(self, files = [], dirs = []):
    self.dirs = dirs
    self.files = files
    self.files_by_lower_basename = {}
    for f in files:
      bn = os.path.basename(f).lower()
      if bn not in self.files_by_lower_basename:
        self.files_by_lower_basename[bn] = []
      self.files_by_lower_basename[bn].append(f)

  def search_basenames(self, basename_query):
    res = []
    lower_basename_query = basename_query.lower()
    for bn in self.files_by_lower_basename.keys():
      if bn.find(lower_basename_query) != -1:
        res.append(bn)
    return res, False

class MockQuery(Query):
  def __init__(self, *args, **kwargs):
    Query.__init__(self, *args, **kwargs)
    self.did_call_execute_nocache = False

  def execute_nocache(self, shard_manager, query_cache):
    self.did_call_execute_nocache = True
    return Query.execute_nocache(self, shard_manager, query_cache)

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

    exact_res = query._filter_result_for_exact_matches("bcd.txt", res)
    self.assertEquals(len(exact_res.ranks), len(exact_res.filenames))
    self.assertEquals(2, len(exact_res.filenames))
    self.assertEquals(["a/bcd.txt", "b/bcd.txt"], exact_res.filenames)

    exact_res = query._filter_result_for_exact_matches("b/bcd.txt", res)
    self.assertEquals(len(exact_res.ranks), len(exact_res.filenames))
    self.assertEquals(1, len(exact_res.filenames))
    self.assertEquals(["b/bcd.txt"], exact_res.filenames)

    exact_res = query._filter_result_for_exact_matches("x/bcd.txt", res)
    self.assertEquals(len(exact_res.ranks), len(exact_res.filenames))
    self.assertEquals(0, len(exact_res.filenames))
    self.assertEquals([], exact_res.filenames)

  def test_global_rank_adjustment_puts_suffixes_into_predictable_order(self):
    # render_widget.cpp should be get re-ranked higher than render_widget.h
    in_res = QueryResult(hits=[("/render_widget.h", 10),
                               ("/render_widget.cpp", 10)])
    res = query._apply_global_rank_adjustment(in_res, ["/"], Query("rw"))
    self.assertEquals(["/render_widget.cpp",
                       "/render_widget.h",], res.filenames)

    # render_widget.cpp should stay ranked higher than render_widget.h
    in_res = QueryResult(hits=[("/render_widget.cpp", 10),
                              ("/render_widget.h", 10)])
    res = query._apply_global_rank_adjustment(in_res, ["/"], Query("rw"))
    self.assertEquals(["/render_widget.cpp",
                       "/render_widget.h"], res.filenames)

    # but if the ranks mismatch, dont reorder
    in_res = QueryResult(hits=[("/render_widget.cpp", 10),
                              ("/render_widget.h", 12)])
    res = query._apply_global_rank_adjustment(in_res, ["/"], Query("rw"))
    self.assertEquals(["/render_widget.h",
                       "/render_widget.cpp"], res.filenames)

  def test_global_rank_adjustment_puts_directories_into_predictable_order(self):
    # and if d if the ranks mismatch, dont reorder
    in_res = QueryResult(hits=[("/b/render_widget.cpp", 10),
                               ("/a/render_widget.cpp", 10)])
    res = query._apply_global_rank_adjustment(in_res, ["/"], Query("rw"))
    self.assertEquals(["/a/render_widget.cpp",
                       "/b/render_widget.cpp"], res.filenames)

  def test_adjustment_puts_current_project_above_noncurrent(self):
    in_res = QueryResult(hits=[("/b/render_widget.cpp", 10),
                               ("/a/render_widget.cpp", 10)])
    res = query._apply_global_rank_adjustment(in_res,
                                       ["/a/", "/b/"],
                                       Query("rw", current_filename="/b/k/foobar.cpp"))
    rA = res.rank_of("/a/render_widget.cpp")
    rB = res.rank_of("/b/render_widget.cpp")
    self.assertTrue(rB > rA, "Expected %s > %s" % (rB, rA))

  def test_rerank(self):
    self.assertEquals([],
                      query._rerank([]))
    self.assertEquals([("a/b.txt", 10)],
                      query._rerank([("a/b.txt", 10)]))
    self.assertEquals([("a/b1.txt", 10),
                       ("a/b2.txt", 9.9),
                       ("a/c.txt", 8.9),
                       ("a/c.txt", 6.9)],
                      query._rerank([("a/b1.txt", 10),
                                     ("a/b2.txt", 10),
                                     ("a/c.txt", 9),
                                     ("a/c.txt", 7)
                                     ]))
    self.assertEquals([("a/b.txt", 10),
                       ("a/x.txt", 9),
                       ("a/y.txt", 8.9)],
                      query._rerank([("a/b.txt", 10),
                                     ("a/x.txt", 9),
                                     ("a/y.txt", 11)]))

  def test_cache_same_maxhits(self):
    q1 = MockQuery("a", 10)
    query_cache = QueryCache()
    shard_manager = FakeDBShardManager()
    q1.execute(shard_manager, query_cache)
    self.assertTrue(q1.did_call_execute_nocache)

    q2 = MockQuery("a", 10)
    q2.execute(shard_manager, query_cache)
    self.assertFalse(q2.did_call_execute_nocache)

  def test_cache_different_maxhits(self):
    q1 = MockQuery("a", 10)
    query_cache = QueryCache()
    shard_manager = FakeDBShardManager()
    q1.execute(shard_manager, query_cache)
    self.assertTrue(q1.did_call_execute_nocache)

    q2 = MockQuery("a", 11)
    q2.execute(shard_manager, query_cache)
    self.assertTrue(q2.did_call_execute_nocache)

  def test_empty_query(self):
    q1 = MockQuery("", 10)
    query_cache = QueryCache()
    shard_manager = FakeDBShardManager()
    q1.execute(shard_manager, query_cache)
    self.assertFalse(q1.did_call_execute_nocache)

  def test_is_dirmatch(self):
    self.assertTrue(query._is_dirmatch("foo", "a/b/foo/"))
    self.assertTrue(query._is_dirmatch("foo", "a/b/foo/c.txt"))
    self.assertFalse(query._is_dirmatch("foo", "a/b/foo/bar/s.txt"))

    self.assertTrue(query._is_dirmatch("foo/bar", "/foo/bar/s.txt"))
    self.assertFalse(query._is_dirmatch("foo/bar", "/foo/bar/a/s.txt"))

  def test_exact_filter_plumbing(self):
    shard_manager = FakeDBShardManager(["foo/bar.txt", "foo/rebar.txt"])
    query_cache = QueryCache()

    res = MockQuery("bar", 10, exact_match=True).execute(shard_manager, query_cache)
    self.assertTrue(res.is_empty())

    res = MockQuery("bar.txt", 10, exact_match=True).execute(shard_manager, query_cache)
    self.assertEquals(["foo/bar.txt"], res.filenames)

  def test_empty_dir_query(self):
    shard_manager = FakeDBShardManager(["foo/bar.txt", "foo/rebar.txt"])
    query_cache = QueryCache()

    res = MockQuery("/").execute(shard_manager, query_cache)
    self.assertTrue(len(res.filenames) != 0)

  def test_dir_only_query(self):
    shard_manager = FakeDBShardManager(["foo/bar.txt", "foo/rebar.txt", "blah/baz.txt"])
    query_cache = QueryCache()

    res = MockQuery("foo/").execute(shard_manager, query_cache)
    self.assertEquals(["foo/bar.txt", "foo/rebar.txt"], res.filenames)

  def test_query_that_times_out(self):
    files = []
    for i in range(100000):
      files.append("f/x%i.txt" % i)
    shard_manager = FakeDBShardManager(files)
    query_cache = QueryCache()
    q = MockQuery("x/")
    q._dir_search_timeout = 0.00001
    res = q.execute(shard_manager, query_cache)
    self.assertTrue(res.truncated)

  def test_basename_only_query(self):
    shard_manager = FakeDBShardManager(["foo/bar.txt", "foo/rebar.txt", "blah/baz.txt"])
    query_cache = QueryCache()

    res = MockQuery("bar").execute(shard_manager, query_cache)
    self.assertEquals(["foo/bar.txt", "foo/rebar.txt"], res.filenames)

  def test_dir_and_basename_query(self):
    shard_manager = FakeDBShardManager(["foo/bar.txt", "foo/rebar.txt", "blah/baz.txt"])
    query_cache = QueryCache()

    res = MockQuery("oo/bar").execute(shard_manager, query_cache)
    self.assertEquals(["foo/bar.txt", "foo/rebar.txt"], res.filenames)

  def test_basename_only_query_rank_results(self):
    basename_ranker = BasenameRanker()
    shard_manager = FakeDBShardManager(["foo/bar.txt", "foo/rebar.txt", "blah/baz.txt"])
    query_cache = QueryCache()

    res = MockQuery("bar").execute_nocache(shard_manager, query_cache)
    self.assertEquals(set(["foo/bar.txt", "foo/rebar.txt"]), set(res.filenames))
    self.assertEquals([basename_ranker.rank_query("bar", os.path.basename(res.filenames[0])),
                       basename_ranker.rank_query("bar", os.path.basename(res.filenames[1]))], res.ranks)

  def test_adjustment_creates_decreasing_hit_order(self):
    initial_result = QueryResult.from_dict({'ranks': [12.0, 10.800000000000001, 9.3000000000000007, 9.3000000000000007, 8.5999999999999996, 7.5, 7.0, 9.3000000000000007, 9.3000000000000007, 10.0, 9.3000000000000007, 7.5, 7.5, 7.5, 7.0, 10.0, 10.0, 7.5, 7.5, 7.5, 7.0, 7.0, 7.5, 7.5, 7.0, 7.5, 7.5, 13.5, 10.5, 14.0, 14.0, 14.0, 7.0, 7.5, 7.5], 'truncated': True, 'filenames': ['/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/fast/js/script-tests/char-at.js', '/Users/nduca/home/quickopen/test_data/cr_files_basenames.json', '/Users/nduca/Local/chrome/src/chrome/browser/resources/options2/instant_confirm_overlay.js', '/Users/nduca/Local/chrome/src/chrome/browser/resources/options/instant_confirm_overlay.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/svg/dynamic-updates/script-tests/SVGCircleElement-dom-requiredFeatures.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/svg/dom/SVGScriptElement/resources/script-set-href-p9pass.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/dom/xhtml/level3/core/domconfigurationcansetparameter03.js', '/Users/nduca/Local/chrome/src/chrome/browser/resources/options2/chromeos/cellular_plan_element.js', '/Users/nduca/Local/chrome/src/chrome/browser/resources/options/chromeos/cellular_plan_element.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/dom/svg/level3/xpath/Conformance_Expressions.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/Source/WebCore/inspector/front-end/ResourceResponseView.js', '/Users/nduca/home/trace_event_viewer/third_party/chrome/shared/js/cr/ui/focus_outline_manager.js', '/Users/nduca/Local/chrome/src/chrome/browser/resources/shared/js/cr/ui/focus_outline_manager.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/svg/dom/SVGScriptElement/resources/script-set-href-p2fail.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/Source/WebCore/inspector/front-end/InspectorView.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/dom/xhtml/level1/core/hc_characterdatadeletedatamiddle.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/dom/html/level1/core/hc_characterdatadeletedatamiddle.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/http/tests/security/xssAuditor/resources/base-href/really-safe-script.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/dom/xhtml/level1/core/hc_attrreplacechild1.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/dom/html/level1/core/hc_attrreplacechild1.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/fast/dom/Geolocation/script-tests/timeout-clear-watch.js', '/Users/nduca/Local/chrome/src/chrome/test/data/extensions/api_test/history/search_after_add.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/svg/dom/SVGScriptElement/resources/script-set-href-p5fail.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/svg/dynamic-updates/script-tests/SVGRectElement-dom-y-attr.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/dom/xhtml/level3/core/documentrenamenode03.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/dom/xhtml/level1/core/hc_textsplittextfour.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/dom/html/level1/core/hc_textsplittextfour.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/fast/dom/Orientation/script-tests/create-event-orientationchange.js', '/Users/nduca/Local/chrome/src/chrome/browser/resources/connection_manager.js', '/Users/nduca/home/trace_event_viewer/third_party/chrome/shared/js/cr.js', '/Users/nduca/Local/chrome/src/chrome/common/extensions/docs/examples/extensions/plugin_settings/domui/js/cr.js', '/Users/nduca/Local/chrome/src/chrome/browser/resources/shared/js/cr.js', '/Users/nduca/Local/chrome/src/third_party/WebKit/LayoutTests/fast/js/mozilla/eval/script-tests/exhaustive-global-strictcaller-indirect-strictcode.js', '/Users/nduca/home/trace_event_viewer/third_party/chrome/shared/js/event_tracker.js', '/Users/nduca/Local/chrome/src/chrome/browser/resources/shared/js/event_tracker.js']})
    dirs = ['/Users/nduca/Local/ndbg', '/Users/nduca/Local/quickopen', '/Users/nduca/home', '/Users/nduca/Local/chrome']
    q = Query("cr.js")
    res = query._apply_global_rank_adjustment(initial_result, dirs, q)
    for i in range(1, len(res.ranks)):
      self.assertTrue(res.ranks[i-1] > res.ranks[i])
    self.assertEquals('/Users/nduca/Local/chrome/src/chrome/browser/resources/shared/js/cr.js', res.filenames[0])
