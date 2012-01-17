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

class DBIndexTestBase(object):
  def setUp(self):
    mock_indexer = db_indexer.MockIndexer('test_data/cr_files_by_basename_five_percent.json')
    self.index = db_index.DBIndex(mock_indexer,threaded=self.threaded)

  def tearDown(self):
    self.index.close()

  def test_case_sensitive_query(self):
    self.assertTrue('~/chrome/src/third_party/tlslite/tlslite/integration/ClientHelper.py' in self.index.search('ClientHelper').hits)

  def test_wordstart_query(self):
    self.assertTrue('~/chrome/src/content/browser/renderer_host/render_widget_host_gtk.cc' in self.index.search('rwh').hits)
    self.assertTrue('~/chrome/src/content/browser/renderer_host/render_widget_host_gtk.cc' in self.index.search('rwhg').hits)

  def test_wordstart_query2(self):
    self.assertTrue('~/chrome/src/third_party/WebKit/Source/WebCore/css/MediaFeatureNames.cpp' in self.index.search('mfn').hits)
    self.assertTrue('~/chrome/src/third_party/WebKit/Source/WebCore/css/MediaFeatureNames.cpp' in self.index.search('MFN').hits)

  def test_case_insensitive_query(self):
    self.assertTrue("~/ndbg/quickopen/src/db_proxy_test.py" in self.index.search('db_proxy_test').hits)
    self.assertTrue("~/ndbg/quickopen/test_data/something/something_file.txt" in self.index.search('something_file.txt').hits)

  def test_case_query_with_extension(self):
    self.assertTrue("~/ndbg/quickopen/src/db_proxy_test.py" in self.index.search('db_proxy_test.py').hits)
    self.assertTrue('~/chrome/src/third_party/tlslite/tlslite/integration/ClientHelper.py' in self.index.search('ClientHelper.py').hits)

  def _assertSetEquals(self, ref,src):
    src_set = set(src)
    ref_set = set(ref)
    if set(ref) != set(src):
      src_only = src_set.difference(ref_set)
      ref_only = ref_set.difference(src_set)
      self.assertEquals(ref_set,src_set)

  def test_dir_query(self):
    src = self.index.search('src/').hits
    ref = [u'~/chrome/src/third_party/sqlite/src/src/analyze.c', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/VideoFrameChromiumImpl.h', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/WorkerFileWriterCallbacksBridge.cpp', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/WebFontImpl.cpp', u'~/chrome/src/third_party/sqlite/src/src/test_journal.c', u'~/chrome/src/third_party/sqlite/src/src/btreeInt.h', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/StorageNamespaceProxy.h', u'~/chrome/src/third_party/WebKit/Tools/iExploder/iexploder-1.7.2/src/config.yaml', u'~/chrome/src/third_party/libxml/src/nanohttp.c', u'~/chrome/src/sandbox/src/sandbox.cc', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/WebFrameImpl.cpp', u'~/chrome/src/third_party/harfbuzz/src/harfbuzz-hangul.c', u'~/chrome/src/third_party/sqlite/src/src/loadext.c', u'~/chrome/src/third_party/sqlite/src/src/test_intarray.h', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/ChromiumOSRandomSource.cpp', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/IDBDatabaseCallbacksProxy.h', u'~/ndbg/quickopen/src/open_dialog_base.py', u'~/chrome/src/third_party/WebKit/Source/ThirdParty/gtest/src/gtest-filepath.cc', u'~/chrome/src/third_party/sqlite/src/mkopcodec.awk', u'~/chrome/src/third_party/sqlite/src/src/fkey.c', u'~/chrome/src/third_party/harfbuzz/src/harfbuzz-shape.h', u'~/chrome/src/third_party/libxml/src/testapi.c', u'~/chrome/src/third_party/sqlite/src/config.guess', u'~/chrome/src/third_party/libxml/src/config.guess', u'~/chrome/src/third_party/libxml/src/check-relaxng-test-suite.py', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/WebEntities.cpp', u'~/chrome/src/third_party/harfbuzz-ng/src/hb-unicode-private.h', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/WebIDBDatabaseError.cpp', u'~/chrome/src/third_party/sqlite/src/src/test_tclvar.c', u'~/chrome/src/third_party/libxml/src/configure.in', u'~/chrome/src/third_party/WebKit/Source/ThirdParty/gyp/test/include_dirs/src/includes.c', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/ExternalPopupMenu.cpp', u'~/chrome/src/sandbox/src/sandbox.vcproj', u'~/ndbg/quickopen/src/db_test.pyc', u'~/chrome/src/third_party/WebKit/Source/ThirdParty/gyp/test/builddir/src/func3.c', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/WebFontDescription.cpp', u'~/chrome/src/sandbox/src/nt_internals.h', u'~/chrome/src/sandbox/src/sid.h', u'~/chrome/src/tools/symsrc/COPYING-pefile', u'~/chrome/src/third_party/harfbuzz-ng/src/hb-common.h', u'~/chrome/src/third_party/sqlite/src/src/pager.h', u'~/chrome/src/AUTHORS', u'~/chrome/src/third_party/libxml/src/AUTHORS', u'~/chrome/src/third_party/tcmalloc/vendor/src/stacktrace_x86_64-inl.h', u'~/chrome/src/third_party/tcmalloc/chromium/src/stacktrace_x86_64-inl.h', u'~/chrome/src/sandbox/src/sandbox_utils.h', u'~/chrome/src/sandbox/src/named_pipe_dispatcher.h', u'~/chrome/src/third_party/WebKit/Source/ThirdParty/gtest/src/gtest-port.cc', u'~/chrome/src/third_party/harfbuzz/src/harfbuzz.c', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/WebDeviceOrientation.cpp', u'~/chrome/src/third_party/sqlite/src/src/pcache1.c', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/WebIDBKey.cpp', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/VideoFrameChromiumImpl.cpp', u'~/ndbg/quickopen/src/dyn_object.pyc', u'~/chrome/src/third_party/sqlite/src/src/test_backup.c', u'~/chrome/src/third_party/tcmalloc/vendor/src/stacktrace_win32-inl.h', u'~/chrome/src/third_party/tcmalloc/chromium/src/stacktrace_win32-inl.h', u'~/ndbg/quickopen/src/db_proxy_test.py']
    self._assertSetEquals(set(ref),set(src))

  def test_emtpy_dir_query(self):
    self.assertEquals([], self.index.search('/').hits)

  def test_two_dir_query(self):
    self.assertTrue("~/ndbg/quickopen/src/db_proxy_test.py" in self.index.search('quickopen/src/').hits)

  def test_dir_and_name_query(self):
    self.assertTrue("~/ndbg/quickopen/src/db_proxy_test.py" in self.index.search('src/db_proxy_test.py').hits)


class DBIndexSearchResultTest(unittest.TestCase):
  def test_is_exact_match_1(self):
    res = db_index.DBIndexSearchResult()
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
    res = db_index.DBIndexSearchResult()
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

class DBIndexTestMT(unittest.TestCase, DBIndexTestBase):
  def setUp(self,*args,**kwargs):
    self.threaded = True
    unittest.TestCase.setUp(self,*args,**kwargs)
    DBIndexTestBase.setUp(self)

  def tearDown(self):
    DBIndexTestBase.tearDown(self)

class DBIndexTestST(unittest.TestCase, DBIndexTestBase):
  def setUp(self,*args,**kwargs):
    unittest.TestCase.setUp(self,*args,**kwargs)
    self.threaded = False
    DBIndexTestBase.setUp(self)

  def test_chunker(self):
    def validate(num_items,nchunks):
      start_list = [(i,True) for i in range(num_items)]
      chunks = self.index._make_chunks(start_list,nchunks)
      found_indices = set()
      for chunk in chunks:
        for i,j in chunk.items():
          self.assertTrue(i not in found_indices)
          found_indices.add(i)
      self.assertEquals(set(range(num_items)), found_indices)
    validate(0,1)
    validate(10,1)
    validate(10,2)
    validate(10,3)

  def tearDown(self):
    DBIndexTestBase.tearDown(self)

class DBIndexPerfTest():
  def __init__(self, testfile):
    mock_indexer = db_indexer.MockIndexer(testfile)
    self.index = db_index.DBIndex(mock_indexer)

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
      self.index.search(q,max_hits)
      elapsed = time.time() - start
      print '%15s %.3f' % (q ,elapsed)
      
if __name__ == '__main__':
  test = DBIndexPerfTest('test_data/cr_files_by_basename.json')
  print "Results for max=30:"
  test.test_matcher_perf(max_hits=30)
  print "\n"
