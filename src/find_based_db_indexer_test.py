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

from src import find_based_db_indexer

class IndexerForTest(find_based_db_indexer.FindBasedDBIndexer):
  def is_ignored(self, filename):
    assert len(self.dirs) == 1
    self.files_by_basename = dict()
    self._process_lines(self.dirs[0], [filename + '\n'])
    basename = os.path.basename(filename)
    if basename not in self.files_by_basename:
      return True
    if filename not in self.files_by_basename[basename]:
      return True
    return False

class FindBasedDBIndexerUnitTests(unittest.TestCase):
  def test_relpath_basic(self):
    x = find_based_db_indexer._get_filename_relative_to_find_dir(
      '/a/b/c',
      '/a/b/c/d')
    self.assertEquals(x, 'd')

  def test_simple_ingore(self):
    indexer = IndexerForTest(['/a/b'],
                             ['*.svn'])
    self.assertFalse(indexer.is_ignored('/a/b/bar'))

  def test_dirname_ingore(self):
    indexer = IndexerForTest(['/a/b'],
                             ['/a/b/c/*'])
    self.assertFalse(indexer.is_ignored('/a/b/bar'))
    self.assertTrue(indexer.is_ignored('/a/b/c/bar'))

  def test_wildcard_ingore(self):
    indexer = IndexerForTest(['/a/b'],
                             ['.svn'])
    self.assertTrue(indexer.is_ignored('/a/b/.svn/foo'))

  def test_wildcard_ingore_2(self):
    indexer = IndexerForTest(['/a/b'],
                             ['.*'])
    self.assertTrue(indexer.is_ignored('/a/b/.svn/bar.baz'))
    self.assertFalse(indexer.is_ignored('/a/b/bar.baz'))

  def test_sequential_wildcard_optimization_1(self):
    indexer = IndexerForTest(['/a/b'],
                             ['.*'])
    self.assertTrue(indexer.is_ignored('/a/b/.svn/bar.baz'))
    self.assertTrue(indexer.is_ignored('/a/b/.svn/blah.baz'))
    self.assertFalse(indexer.is_ignored('/a/b/blah.baz'))

  def test_sequential_wildcard_optimization_2(self):
    indexer = IndexerForTest(['/a/b'],
                             ['*.o'])
    self.assertTrue(indexer.is_ignored('/a/b/foo.o'))
    self.assertFalse(indexer.is_ignored('/a/b/foo.o.d'))

  def test_multiple_dirs(self):
    indexer = IndexerForTest(['/a/b',
                              '/c'],
                             [])
    n = [0]
    stubbed_fn = indexer._did_finish_searching_dir
    def stub():
      n[0] += 1
      stubbed_fn()
      return []
    indexer._did_finish_searching_dir = stub
    while not indexer.complete:
      indexer.index_a_bit_more()
    self.assertEquals(n[0], 2)


class BasenameLevelFilterTest(unittest.TestCase):
  def test_1(self):
    pred = find_based_db_indexer._MakeIgnorePredicate(["*.o"])
    filter = find_based_db_indexer._BasenameLevelFilter(pred)
    assert filter.match_filename("src/out/foo.o") == True
    assert filter.match_filename("src/out/foo.o.d") == False

  def test_2(self):
    pred = find_based_db_indexer._MakeIgnorePredicate(["out"])
    filter = find_based_db_indexer._BasenameLevelFilter(pred)
    assert filter.match_filename("src/out/foo.txt") == True
    assert filter.match_filename("src/out/bar.txt") == True
    assert filter.match_filename("src/xyz/wxy/z.txt") == False

class DirectoryLevelFilterTest(unittest.TestCase):
  def test_1(self):
    pred = find_based_db_indexer._MakeIgnorePredicate(["a/b/c/*"])
    filter = find_based_db_indexer._DirectoryLevelFilter(pred)
    assert filter.match_filename("a/b/x.txt") == False
    assert filter.match_filename("a/b/c/x.txt") == True
    assert filter.match_filename("a/b/c/y.txt") == True
    assert filter.match_filename("a/b/d.txt") == False
    assert filter.match_filename("a/b/c/y.txt") == True
    assert filter.match_filename("a/b/x/y/z.txt") == False

  def test_2(self):
    pred = find_based_db_indexer._MakeIgnorePredicate(["*out/*"])
    filter = find_based_db_indexer._DirectoryLevelFilter(pred)
    assert filter.match_filename("a/b/x.txt") == False
    assert filter.match_filename("a/out/x.txt") == True
    assert filter.match_filename("a/out/foo/y.txt") == True
    assert filter.match_filename("out/b/d.txt") == True
