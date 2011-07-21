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
import db_index
import db_indexer
import sys
import unittest
import time

FILES_BY_BASENAME = None
QUERIES = [
  'warmup',
  'r',
  'rw',
  'rwh',
  'rwhv',
  're',
  'ren',
  'rend',
  'rende',
  'render',
  'render_',
  'render_w',
  'render_wi',
  'render_widget',
  'iv',
  'info_view',
  'w',
  'we',
  'web',
  'webv',
  'webvi',
  'webvie',
  'webview',
  'wv',
  'wvi',
  'webgraphics'
  ]

class DBIndexTestBase(object):
  def __init__(self, test_file):
    mock_indexer = db_indexer.MockIndexer(test_file)
    matchers = db_index.matchers()
    self.indexers = {}
    for (mn, m) in matchers.items():
      self.indexers[mn] = db_index.DBIndex(mock_indexer, mn)

class DBIndexTest(unittest.TestCase,DBIndexTestBase):
  def __init__(self,*args,**kwargs):
    unittest.TestCase.__init__(self,*args,**kwargs)
    DBIndexTestBase.__init__(self, 'test_data/cr_files_by_basename_five_percent.json')

  def test_matchers_agree_on_all_queries(self):
    for q in QUERIES:
      res = []
      for mn,i in self.indexers.items():
        res.append(i.search(q,max_hits=sys.maxint))

      for i in range(1,len(res)):
        a = set(res[i-1].hits)
        b = set(res[i].hits)
        if a != b:
          # debug only
          a_name = db_index.matchers().keys()[i-1]
          b_name = db_index.matchers().keys()[i]
          in_a = a.difference(b)
          in_b = b.difference(a)
          import pdb; pdb.set_trace()
          self.assertTrue(False)

class DBIndexPerfTest(DBIndexTestBase):
  def test_matcher_perf(self,max_hits):
    header_rec = ["  %15s "]
    header_data = ["query"]
    entry_rec = ["  %15s "]
    for mn in self.indexers.keys():
      header_rec.append("%10s")
      header_data.append(mn)
      entry_rec.append("%10.4f")
    print ' '.join(header_rec) % tuple(header_data)
    for q in QUERIES:
      entry_data = [q]
      for mn,i in self.indexers.items():
        start = time.time()
        i.search(q,max_hits)
        elapsed = time.time() - start
        entry_data.append(elapsed)
      print ' '.join(entry_rec) % tuple(entry_data)
      
if __name__ == '__main__':
  test = DBIndexPerfTest('test_data/cr_files_by_basename.json')
  print "Results for max=30:"
  test.test_matcher_perf(max_hits=30)
  print "\n"
