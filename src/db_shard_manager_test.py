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
import sys
import unittest
import time

from src import db_shard_manager
from src import mock_db_indexer

from query import Query
from query_cache import QueryCache

class DBShardManagerTest(unittest.TestCase):
  def setUp(self,*args,**kwargs):
    self.files = [
        "a/b/csdf.txt",
        "a/b/ghijkl.txt",
        "a/dsfsfd.txt",
        "k/dsfsfd.txt",
        "k/sdf.txt",
        ]
    mock_indexer = mock_db_indexer.MockDBIndexer(["a/", "k/"], self.files)
    self.shard_manager = db_shard_manager.DBShardManager(mock_indexer)

  def test_props(self):
    self.assertEquals(set(self.files),set(self.shard_manager.files))
    self.assertEquals(set(["a/dsfsfd.txt", "k/dsfsfd.txt"]),
                      set(self.shard_manager.files_by_lower_basename["dsfsfd.txt"]))

  def test_smoketest_basename_search(self):
    """
    Does a very simple smoketest on the shard search.
    """
    res, truncated = self.shard_manager.search_basenames("sdf")
    self.assertEquals(set(["csdf.txt", "sdf.txt"]), set(res))
    self.assertFalse(truncated)

  def test_chunker(self):
    def validate(num_items,nchunks):
      start_list = [i for i in range(num_items)]
      chunks = self.shard_manager._make_chunks(start_list,nchunks)
      found_indices = set()
      for chunk in chunks:
        for i in chunk:
          self.assertTrue(i not in found_indices)
          found_indices.add(i)
      self.assertEquals(set(range(num_items)), found_indices)
    validate(0,1)
    validate(10,1)
    validate(10,2)
    validate(10,3)

  def tearDown(self):
    self.shard_manager.close()

class DBShardManagerPerfTest():
  def __init__(self, testfile):
    files_by_basename = json.load(open(filename))
    mock_indexer = mock_db_indexer.MockDBIndexer(files_by_basename = files_by_basename)
    self.shard_manager = db_shard_manager.DBShardManager(mock_indexer)

  def test_matcher_perf(self,max_hits):
    print "%15s %s" % ("query", "time")

    PERF_QUERIES = [
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
    for q in PERF_QUERIES:
      start = time.time()
      self.shard_manager.search(q,max_hits)
      elapsed = time.time() - start
      print '%15s %.3f' % (q ,elapsed)

if __name__ == '__main__':
  test = DBShardManagerPerfTest('test_data/cr_files_by_basename.json')
  print "Results for max=30:"
  test.test_matcher_perf(max_hits=30)
  print "\n"
