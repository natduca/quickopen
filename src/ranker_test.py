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
from ranker import Ranker
import matcher

class RankerTest(unittest.TestCase):
  def setUp(self):
#    self.basenames = json.load(open('test_data/cr_files_basenames.json'))
    self.ranker = Ranker()

  def test_is_wordstart(self):
    def check(s, expectations):
      assert len(s) == len(expectations)
      for i in range(len(s)):
        self.assertEquals(expectations[i], self.ranker._is_wordstart(s, i), "disagreement on index %i" % i)

    check("foo", [True, False, False])
    check("fooBar", [True, False, False, True, False, False])
    check("o", [True])
    check("_", [True])
    check("F", [True])
    check("FooBar", [True, False, False, True, False, False])
    check("Foo_Bar", [True, False, False, False, True, False, False])
    check("_Bar", [True, True, False, False])
    check("_bar", [True, True, False, False])
    check("foo_bar", [True, False, False, False, True, False, False])

    check(".h", [True, False])
    check("a.h", [True, False, False])
    check("__b", [True, False, True])
    check("foo__bar", [True, False, False, False, False, True, False, False])

    check("Foo3D", [True, False, False, True, True])
    check("Foo33", [True, False, False, True, False])

    check("x3d", [True, True,  False]) # I could be convinced that 'd' is a wordstart.

    check("AAb", [True, True, False])
    check("CCFra", [True, True, True, False, False])

  def test_get_word_starts(self):
    data = {
      # This comment simply helps map indice to values
      # 1234567
      '' : [],
      'abc' : [0],
      'abd_def' : [0, 4],
      'ab_cd_ef' : [0, 3, 6],
      'ab_' : [0],
      'AA': [0, 1],
      'AAbA': [0,1,3],
      'Abc': [0],
      'AbcDef': [0,3],
      'Abc_Def': [0,4],
      }
    for word, expected_starts in data.items():
      starts = self.ranker.get_starts(word)
      self.assertEquals(expected_starts, starts, "for %s, expect %s" % (word, expected_starts))

  def assertBasicRankAndWordHitCountIs(self, expected_rank, expected_word_count, query, candidate):
    res = self.ranker._get_basic_rank(query, candidate)
    self.assertEquals(expected_rank, res[0])
    self.assertEquals(expected_word_count, res[1])

  def test_query_hits_on_word_starts(self):
    self.assertBasicRankAndWordHitCountIs(8, 4, 'rwhv', 'render_widget_host_view.cc') # test +1 for hitting all words
    self.assertBasicRankAndWordHitCountIs(6, 3, 'rwh', 'render_widget_host_view.cc')
    self.assertBasicRankAndWordHitCountIs(5.5, 2, 'wvi', 'render_widget_host_view_win.cc') # eew
    self.assertBasicRankAndWordHitCountIs(2, 1, 'w', 'WebViewImpl.cc')
    self.assertBasicRankAndWordHitCountIs(2, 1, 'v', 'WebViewImpl.cc')
    self.assertBasicRankAndWordHitCountIs(4, 2, 'wv', 'WebViewImpl.cc')
    self.assertBasicRankAndWordHitCountIs(5, 2, 'evi', 'WebViewImpl.cc')
    self.assertBasicRankAndWordHitCountIs(4, 2, 'wv', 'eWbViewImpl.cc')
    self.assertBasicRankAndWordHitCountIs(6, 0, 'ebewp', 'WebViewImpl.cc')


  def test_basic_rank_pays_attention_to_case(self):
    # these test that we aren't losing catching case transpitions
    self.assertBasicRankAndWordHitCountIs(4.5, 1, "rw", "rwf")
    self.assertBasicRankAndWordHitCountIs(4, 2, "rw", "rWf")

  def test_basic_rank_works_at_all(self):
    # these are generic tests
    self.assertBasicRankAndWordHitCountIs(8, 4, "rwhv", "render_widget_host_view.h")
    self.assertBasicRankAndWordHitCountIs(10, 5, "rwhvm", "render_widget_host_view_mac.h")
    self.assertBasicRankAndWordHitCountIs(10, 5, "rwhvm", "render_widget_host_view_mac.mm")

    self.assertBasicRankAndWordHitCountIs(29, 4, 'ccframerate', 'CCFrameRateController.cpp')


  def test_basic_rank_query_case_doesnt_influence_rank_query(self):
    a = self.ranker._get_basic_rank("Rwhvm", "render_widget_host_view_mac.h")
    b = self.ranker._get_basic_rank("rwhvm", "Render_widget_host_view_mac.h")
    self.assertEquals(a, b)

  def test_basic_rank_isnt_only_greedy(self):
    # this checks that we consider _mac and as a wordstart rather than macmm
    self.assertBasicRankAndWordHitCountIs(10, 5, "rwhvm", "render_widget_host_view_macmm")

  def test_basic_rank_on_corner_cases(self):
    self.assertBasicRankAndWordHitCountIs(0, 0, "", "")
    self.assertBasicRankAndWordHitCountIs(0, 0, "", "x")
    self.assertBasicRankAndWordHitCountIs(0, 0, "x", "")
    self.assertBasicRankAndWordHitCountIs(2, 1, "x", "x")
    self.assertBasicRankAndWordHitCountIs(1, 0, "x", "yx")
    self.assertBasicRankAndWordHitCountIs(0, 0, "x", "abcd")

  def test_basic_rank_on_mixed_wordstarts_and_full_words(self):
    self.assertBasicRankAndWordHitCountIs(17, 3, "enderwhv", "render_widget_host_view.h")
    self.assertBasicRankAndWordHitCountIs(15, 2, "idgethv", "render_widget_host_view.h")

    self.assertBasicRankAndWordHitCountIs(8, 4, "rwhv", "render_widget_host_view_mac.h")
    self.assertBasicRankAndWordHitCountIs(14, 5, "rwhvmac", "render_widget_host_view_mac.h")

    self.assertBasicRankAndWordHitCountIs(10, 5, "rwhvm", "render_widget_host_view_mac.h")

  def test_basic_rank_overconditioned_query(self):
    self.assertBasicRankAndWordHitCountIs(2, 1, 'test_thread_tab.py', 'tw')

  def test_rank_corner_cases(self):
    # empty
    self.assertEquals(0, self.ranker.rank_query('foo', ''))
    self.assertEquals(0, self.ranker.rank_query('', 'foo'))

    # undersized
    self.assertEquals(0, self.ranker.rank_query('foo', 'm'))
    self.assertEquals(0, self.ranker.rank_query('f', 'oom'))

    # overconditioned
    self.assertEquals(2, self.ranker.rank_query('test_thread_tab.py', 'tw'))

  def test_rank_subclasses_lower_ranked_than_base(self):
    # this tests that hitting all words counts higher than hitting some of the words
    base_rank = self.ranker.rank_query("rwhvm", "render_widget_host_view.h")
    subclass_rank = self.ranker.rank_query("rwhvm", "render_widget_host_view_subclass.h")
    self.assertTrue(base_rank > subclass_rank)

  def test_rank_order_for_hierarchy_puts_bases_first(self):
    names = ['render_widget_host_view_mac.h',
             'render_widget_host_view_mac.mm',
             'render_widget_host_view_mac_delegate.h',
             'render_widget_host_view_mac_unittest.mm',
             'render_widget_host_view_mac_editcommand_helper.mm',
             'render_widget_host_view_mac_editcommand_helper.h'
             'render_widget_host_view_mac_editcommand_helper_unittest.mm',
             ]
    self._assertRankDecreasesOrStaysTheSame("rwhvm", names)

  def _assertRankDecreasesOrStaysTheSame(self, query, names):
    """
    Makes suer that the first element in the array has highest rank
    and subsequent items have decreasing or equal rank.
    """
    ranks = [self.ranker.rank_query(query, n) for n in names]
    nw = [self.ranker.get_num_words(n) for n in names]
    basic_ranks = [self.ranker._get_basic_rank(query, n) for n in names]
    for i in range(1, len(ranks)):
      changeInRank = ranks[i] - ranks[i-1]
      self.assertTrue(changeInRank <= 0)

  def test_rank_order_prefers_capitals(self):
    # Ensure we still prefer capitals for simple queries The heuristics that
    # deal with order_puts_tests_second tends to break this.
    self.assertBasicRankAndWordHitCountIs(6, 3, 'wvi', 'WebViewImpl.cc')

  def test_rank_order_puts_tests_second(self):
    q = "ccframerate"
    a1 = self.ranker.rank_query(q, 'CCFrameRateController.cpp')
    a2 = self.ranker.rank_query(q, 'CCFrameRateController.h')
    b = self.ranker.rank_query(q, 'CCFrameRateControllerTest.cpp')

    # This is a hard test to pass because ccframera(te) ties to (Te)st
    # if you weight non-word matches equally.
    self.assertTrue(a1 > b);
    self.assertTrue(a2 > b);

    q = "chrome_switches"
    a1 = self.ranker.rank_query(q, 'chrome_switches.cc')
    a2 = self.ranker.rank_query(q, 'chrome_switches.h')
    b = self.ranker.rank_query(q, 'chrome_switches_uitest.cc')
    self.assertTrue(a1 > b);
    self.assertTrue(a2 > b);

  def test_rank_order_for_hierarchy_puts_prefixed_second(self):
    q = "ccframerate"
    a = self.ranker.rank_query(q, 'CCFrameRateController.cpp')
    b1 = self.ranker.rank_query(q, 'webcore_platform.CCFrameRateController.o.d')
    b2 = self.ranker.rank_query(q, 'webkit_unit_tests.CCFrameRateControllerTest.o.d')
    self.assertTrue(a > b1);
    # FAILS because ccframera(te) ties to (Te)st
    # self.assertTrue(a > b2);

  def test_rank_order_puts_tests_second_2(self):
    q = "ccdelaybassedti"
    a1 = self.ranker.rank_query(q, 'CCDelayBasedTimeSource.cpp')
    a2 = self.ranker.rank_query(q, 'CCDelayBasedTimeSource.h')
    b = self.ranker.rank_query(q, 'CCDelayBasedTimeSourceTest.cpp')
    self.assertTrue(a1 > b);
    self.assertTrue(a2 > b);

    q = "LayerTexture"
    a = self.ranker.rank_query(q, 'LayerTexture.cpp')
    b = self.ranker.rank_query(q, 'LayerTextureSubImage.cpp')
    self.assertTrue(a > b)

  def test_refinement_improves_rank_query(self):
    a = self.ranker.rank_query('render_', 'render_widget.cc')
    b = self.ranker.rank_query('render_widget', 'render_widget.cc')
    self.assertTrue(b > a)

  def test_rank_sort_and_adjustment_puts_suffixes_into_predictable_order(self):
    # render_widget.cpp should be get re-ranked higher than render_widget.h
    adj = self.ranker.sort_and_adjust_ranks_given_complete_hit_list([
        ("render_widget.h", 10),
        ("render_widget.cpp", 10),
        ])
    self.assertEquals([("render_widget.cpp", 10),
                       ("render_widget.h", 10)], adj)

    # render_widget.cpp should stay ranked higher than render_widget.h
    adj = self.ranker.sort_and_adjust_ranks_given_complete_hit_list([
        ("render_widget.cpp", 10),
        ("render_widget.h", 10),
        ])
    self.assertEquals([("render_widget.cpp", 10),
                       ("render_widget.h", 10)], adj)

    # but if the ranks mismatch, dont reorder
    adj = self.ranker.sort_and_adjust_ranks_given_complete_hit_list([
        ("render_widget.cpp", 10),
        ("render_widget.h", 12),
        ])
    self.assertEquals([("render_widget.h", 12),
                       ("render_widget.cpp", 10)], adj)

  def test_rank_sort_and_adjustment_puts_directories_into_predictable_order(self):
    # and if d if the ranks mismatch, dont reorder
    adj = self.ranker.sort_and_adjust_ranks_given_complete_hit_list([
        ("b/render_widget.cpp", 10),
        ("a/render_widget.cpp", 10),
        ])
    self.assertEquals([("a/render_widget.cpp", 10),
                       ("b/render_widget.cpp", 10)], adj)


