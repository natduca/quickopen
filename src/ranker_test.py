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

    check(".h", [True, True])
    check("a.h", [True, False, True])
    check("__b", [True, False, True])
    check("foo__bar", [True, False, False, False, False, True, False, False])

    check("AAb", [True, False, False])

  def test_get_word_starts(self):
    data = {
      # This comment simply helps map indice to values
      # 1234567
      '' : [],
      'abc' : [0],
      'abd_def' : [0, 4],
      'ab_cd_ef' : [0, 3, 6],
      'ab_' : [0],
      'AA': [0],
      'AAbA': [0,3],
      'Abc': [0],
      'AbcDef': [0,3],
      'Abc_Def': [0,4],
      }
    for word, expected_starts in data.items():
      starts = self.ranker.get_starts(word)
      self.assertEquals(expected_starts, starts)

  def test_query_hits_on_word_starts(self):
    self.assertEquals((8,4), self.ranker._get_basic_rank('rwhv', 'render_widget_host_view.cc')) # test +1 for hitting all words
    self.assertEquals((6,3), self.ranker._get_basic_rank('rwh', 'render_widget_host_view.cc'))
    self.assertEquals((5,2), self.ranker._get_basic_rank('wvi', 'render_widget_host_view_win.cc')) # eew
    self.assertEquals((2,1), self.ranker._get_basic_rank('w', 'WebViewImpl.cc'))
    self.assertEquals((2,1), self.ranker._get_basic_rank('v', 'WebViewImpl.cc'))
    self.assertEquals((4,2), self.ranker._get_basic_rank('wv', 'WebViewImpl.cc'))
    self.assertEquals((6,3), self.ranker._get_basic_rank('wvi', 'WebViewImpl.cc'))
    self.assertEquals((5,2), self.ranker._get_basic_rank('evi', 'WebViewImpl.cc'))
    self.assertEquals((4,2), self.ranker._get_basic_rank('wv', 'eWbViewImpl.cc'))
    self.assertEquals((5,0), self.ranker._get_basic_rank('ebewp', 'WebViewImpl.cc'))


  def test_basic_rank_pays_attention_to_case(self):
    # these test that we aren't losing catching case transpitions
    self.assertEquals((3,1), self.ranker._get_basic_rank("rw", "rwf"))
    self.assertEquals((4,2), self.ranker._get_basic_rank("rw", "rWf"))

  def test_basic_rank_works_at_all(self):
    # these are generic tests
    self.assertEquals((8,4), self.ranker._get_basic_rank("rwhv", "render_widget_host_view.h"))
    self.assertEquals((10,5), self.ranker._get_basic_rank("rwhvm", "render_widget_host_view_mac.h"))
    self.assertEquals((10,5), self.ranker._get_basic_rank("rwhvm", "render_widget_host_view_mac.mm"))

  def test_basic_rank_query_case_doesnt_influence_rank(self):
    a = self.ranker._get_basic_rank("Rwhvm", "render_widget_host_view_mac.h")
    b = self.ranker._get_basic_rank("rwhvm", "Render_widget_host_view_mac.h")
    self.assertEquals(a, b)

  def test_basic_rank_isnt_only_greedy(self):
    # this checks that we consider _mac and as a wordstart rather than macmm
    self.assertEquals((10, 5), self.ranker._get_basic_rank("rwhvm", "render_widget_host_view_macmm"))

  def test_basic_rank_on_corner_cases(self):
    self.assertEquals((0, 0), self.ranker._get_basic_rank("", ""))
    self.assertEquals((0, 0), self.ranker._get_basic_rank("", "x"))
    self.assertEquals((0, 0), self.ranker._get_basic_rank("x", ""))
    self.assertEquals((2, 1), self.ranker._get_basic_rank("x", "x"))
    self.assertEquals((1, 0), self.ranker._get_basic_rank("x", "yx"))
    self.assertEquals((0, 0), self.ranker._get_basic_rank("x", "abcd"))

  def test_basic_rank_on_mixed_wordstarts_and_full_words(self):
    self.assertEquals((11, 3), self.ranker._get_basic_rank("enderwhv", "render_widget_host_view.h"))
    self.assertEquals((9, 2), self.ranker._get_basic_rank("idgethv", "render_widget_host_view.h"))

    self.assertEquals((8, 4), self.ranker._get_basic_rank("rwhv", "render_widget_host_view_mac.h"))
    self.assertEquals((12, 5), self.ranker._get_basic_rank("rwhvmac", "render_widget_host_view_mac.h"))

    self.assertEquals((10, 5), self.ranker._get_basic_rank("rwhvm", "render_widget_host_view_mac.h"))

  def test_basic_rank_overconditioned_query(self):
    self.assertEquals((2, 1), self.ranker._get_basic_rank('test_thread_tab.py', 'tw'))

  def test_basic_rank_on_suffixes_of_same_base(self):
    # render_widget.cpp should be ranked higher than render_widget.h
    # unless the query explicitly matches the .h or .cpp
    pass

  def test_rank_corner_cases(self):
    # empty
    self.assertEquals(0, self.ranker.rank('foo', ''))
    self.assertEquals(0, self.ranker.rank('', 'foo'))

    # undersized
    self.assertEquals(0, self.ranker.rank('foo', 'm'))
    self.assertEquals(0, self.ranker.rank('f', 'oom'))

    # overconditioned
    self.assertEquals(2, self.ranker.rank('test_thread_tab.py', 'tw'))

  def test_rank_subclasses_lower_ranked_than_base(self):
    # this tests that hitting all words counts higher than hitting some of the words
    base_rank = self.ranker.rank("rwhvm", "render_widget_host_view.h")
    subclass_rank = self.ranker.rank("rwhvm", "render_widget_host_view_subclass.h")
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
    ranks = [self.ranker.rank(query, n) for n in names]
    nw = [self.ranker.get_num_words(n) for n in names]
    basic_ranks = [self.ranker._get_basic_rank(query, n) for n in names]
    for i in range(1, len(ranks)):
      changeInRank = ranks[i] - ranks[i-1]
      self.assertTrue(changeInRank <= 0)
  
  def test_refinement_improves_rank(self):
    a = self.ranker.rank('render_', 'render_widget.cc')
    b = self.ranker.rank('render_widget', 'render_widget.cc')
    self.assertTrue(b > a)

