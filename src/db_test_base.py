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
import db
import os
import test_data

# TODO, some of this stuff into db_indexer test

class DBTestBase(object):
  def setUp(self):
    self.test_data = test_data.TestData()
    self.test_data_dir = self.test_data.test_data_dir

  def tearDown(self):
    self.test_data.close()

  def test_dirs(self):
    d1 = os.path.join(self.test_data_dir, 'project1')
    d2 = os.path.join(self.test_data_dir, 'something')
    d3 = os.path.join(self.test_data_dir, 'xxx')
    self.assertEquals([], self.db.dirs)

    d1_ = self.db.add_dir(d1)
    self.assertEquals([d1_], self.db.dirs)
    self.assertEquals(d1_.path, d1)

    d2_ = self.db.add_dir(d2)
    self.assertEquals([d1_, d2_], self.db.dirs)

    self.db.delete_dir(d1_)
    self.assertEquals([d2_], self.db.dirs)

    d3_ = self.db.add_dir(d3)
    self.assertEquals([d2_, d3_], self.db.dirs)

    self.db.delete_dir(d3_)
    self.assertEquals([d2_], self.db.dirs)

  def test_nonexistant_dir(self):
    self.db.add_dir(self.test_data_dir)
    bad_dir = os.path.join(self.test_data_dir, 'xxx')
    self.db.sync()

  def test_add_nested_dir_doesnt_dup(self):
    self.db.add_dir(self.test_data_dir)
    sub_dir = os.path.join(self.test_data_dir, 'project1')
    self.db.add_dir(sub_dir)
    self.assertEquals(False, self.db.is_syncd)
    self.db.sync()
    res = self.db.search('MySubSystem.c')
    self.assertEquals(1, len(res.hits))    
    self.assertEquals(os.path.join(self.test_data_dir, 'project1/MySubSystem.c'), res.hits[0])

  def test_dir_query(self):
    self.db.add_dir(self.test_data_dir)
    sub_dir = os.path.join(self.test_data_dir, 'project1/')
    self.db.add_dir(sub_dir)
    self.assertEquals(False, self.db.is_syncd)
    self.db.sync()
    res = self.db.search('MySubSystem.c')
    self.assertTrue(len(res.hits) >= 1)
    self.assertTrue(os.path.join(self.test_data_dir, 'project1/MySubSystem.c') in res.hits)

  def test_search_unique(self):
    self.db.add_dir(self.test_data_dir)
    self.assertEquals(False, self.db.is_syncd)
    self.db.sync()
    res = self.db.search('MySubSystem.c')
    self.assertEquals(1, len(res.hits))
    self.assertEquals(os.path.join(self.test_data_dir, 'project1/MySubSystem.c'), res.hits[0])

  def test_search_with_dir(self):
    self.db.add_dir(self.test_data_dir)
    self.assertEquals(False, self.db.is_syncd)
    self.assertFalse(self.db.sync_status().is_syncd)
    self.assertTrue(self.db.sync_status().status != '')
    self.db.sync()
    res = self.db.search('project1/MySubSystem.c')
    self.assertEquals(1, len(res.hits))
    self.assertEquals(os.path.join(self.test_data_dir, 'project1/MySubSystem.c'), res.hits[0])

  def test_partial_search(self):
    self.db.add_dir(self.test_data_dir)
    self.assertEquals(False, self.db.is_syncd)
    self.db.sync()
    res = self.db.search('MyClass')
    self.assertTrue(len(res.hits) >= 2)
    self.assertTrue(os.path.join(self.test_data_dir, 'project1/MyClass.c') in res.hits)
    self.assertTrue(os.path.join(self.test_data_dir, 'project1/MyClass.h') in res.hits)

  def test_dir_symlinks_dont_dup(self):
    pass

  def test_ignores(self):
    self.db.add_dir(self.test_data_dir)
    self.assertEquals(False, self.db.is_syncd)
    self.db.sync()

    # .git should not be found
    res = self.db.search('packed-refs')
    self.assertEquals(0, len(res.hits))

    # file inside .svn should not be found
    res = self.db.search('svn_should_not_show_up.txt')
    self.assertEquals(0, len(res.hits))

    # certain ignored suffixes should not be found
    self.assertEquals([], self.db.search('ignored.o').hits)
    self.assertEquals([], self.db.search('ignored.pyc').hits)
    self.assertEquals([], self.db.search('ignored.pyo').hits)

  def test_ignore_path(self):
    # test ignore of absolute path
    self.db.add_dir(self.test_data_dir)
    self.db.ignore(os.path.join(self.test_data_dir, 'something/*'))
    self.db.sync()
    self.assertEquals([], self.db.search('something_file.txt').hits)

  def test_ignore_inside_symlink(self):
    # the case of interest here is where someone has
    # /project1_symlink_dir --> /project1
    # /project1_symlink is the one requested to be indexed
    # and they ask to ignore something inside the symlink

    # set up so that 
    project1_symlink_dir = os.path.join(self.test_data_dir, "project1_symlink/")
    self.db.add_dir(project1_symlink_dir)
    self.db.sync()

    ref_file = os.path.join(self.test_data_dir, "project1/module/project1_module1.txt")

    # first make sure it shows up via project1_symlink at the non-symlink location
    hits = self.db.search('project1_module1.txt').hits
    self.assertTrue(ref_file in hits)

    # now ignore something inside project1_symlink
    self.db.ignore(os.path.join(self.test_data_dir, 'project1_symlink/module/*'))
    self.db.sync()
    hits = self.db.search('project1_module1.txt').hits
    self.assertTrue(ref_file not in hits)

  def test_ignore_ctl(self):
    self.db.add_dir(self.test_data_dir)
    self.db.sync()

    res = self.db.search('svn_should_not_show_up.txt')
    self.assertEquals(0, len(res.hits))

    orig = list(self.db.ignores)
    for i in orig:
      self.db.unignore(i)
    self.assertEquals(False, self.db.is_syncd)
    self.db.sync()

    res = self.db.search('svn_should_not_show_up.txt')
    self.assertEquals(1, len(res.hits))

    for i in orig:
      self.db.ignore(i)
    self.assertEquals(False, self.db.is_syncd)
    self.db.sync()

    res = self.db.search('svn_should_not_show_up.txt')
    self.assertEquals(0, len(res.hits))

  def test_sync(self):
    self.db.add_dir(self.test_data_dir)
    self.assertEquals(False, self.db.is_syncd)
    self.db.sync()
    self.assertEquals(True, self.db.is_syncd)

  def test_sync(self):
    self.db.add_dir(self.test_data_dir)
    self.assertEquals(False, self.db.is_syncd)
    self.db.sync()
    self.assertEquals(True, self.db.is_syncd)

  def test_search_unsync(self):
    self.db.add_dir(self.test_data_dir)
    self.assertEquals(False, self.db.is_syncd)
    self.assertRaises(db.NotSyncdException, lambda: self.db.search("foo"))

  def test_dup_ignore_ctl(self):
    self.db.add_dir(self.test_data_dir)
    seq = set(self.db.ignores)
    seq.add("foo")
    self.db.ignore("foo")
    self.db.ignore("foo")
    self.assertEquals(seq, set(self.db.ignores))

    self.db.unignore("foo")
    self.assertRaises(Exception, lambda: self.db.unignore("foo"))
    self.assertEquals(False, self.db.is_syncd)
