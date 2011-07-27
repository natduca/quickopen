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

  def test_get_word_starts(self):
    data = {
#      01234567
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

  def test_tricky_situations(self):
    self.assertEquals(0, self.ranker.rank('foo', ''))
    self.assertEquals(0, self.ranker.rank('foo', 't'))
    self.assertEquals(2, self.ranker.rank('test_thread_tab.py', 'tw'))

  def test_query_hits_on_word_starts(self):
    self.assertEquals(6, self.ranker.get_num_hits_on_word_starts('rwhv', 'render_widget_host_view.cc')) # test +1 for hitting all words
    self.assertEquals(4, self.ranker.get_num_hits_on_word_starts('rwh', 'render_widget_host_view.cc'))
    self.assertEquals(3, self.ranker.get_num_hits_on_word_starts('wvi', 'render_widget_host_view_win.cc')) # eew
    self.assertEquals(2, self.ranker.get_num_hits_on_word_starts('w', 'WebViewImpl.cc'))
    self.assertEquals(1, self.ranker.get_num_hits_on_word_starts('v', 'WebViewImpl.cc'))
    self.assertEquals(3, self.ranker.get_num_hits_on_word_starts('wv', 'WebViewImpl.cc'))
    self.assertEquals(5, self.ranker.get_num_hits_on_word_starts('wvi', 'WebViewImpl.cc'))
    self.assertEquals(2, self.ranker.get_num_hits_on_word_starts('evi', 'WebViewImpl.cc'))
    self.assertEquals(2, self.ranker.get_num_hits_on_word_starts('wv', 'eWbViewImpl.cc'))
    self.assertEquals(1, self.ranker.get_num_hits_on_word_starts('ebiew', 'WebViewImpl.cc'))

  def test_rank(self):
    self.assertEquals(3, self.ranker.rank('render_', 'render_widget.cc'))
    self.assertEquals(8, self.ranker.rank('render_widget', 'render_widget.cc'))
