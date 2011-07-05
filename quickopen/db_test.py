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
import settings
import tempfile
import unittest

class DBTest(unittest.TestCase):
  def setUp(self):
    self.settings_file = tempfile.NamedTemporaryFile()
    self.settings = settings.Settings(self.settings_file.name)
    self.db = db.DB(self.settings)

    # create a directory hierarchy to do tests in
    self.test_data_dir = os.path.realpath(os.path.join(tempfile.gettempdir(), 'db_test'))
    if os.path.exists(self.test_data_dir):
      os.system('rm -rf %s' % self.test_data_dir)
    os.system('cp -r ./test_data/ %s' % self.test_data_dir)

    # dir symlink project1_symlink to project1
    src = os.path.join(self.test_data_dir, 'project1')
    dst = os.path.join(self.test_data_dir, 'project1_symlink')
    os.system('ln -s %s %s' % (src, dst))

    # file symlink something/foo.txt to project1/something/foo.txt
    src = os.path.join(self.test_data_dir, 'project1/foo.txt')
    dst = os.path.join(self.test_data_dir, 'something/foo.txt')
    os.system('ln -s %s %s' % (src, dst))


  def tearDown(self):
    if os.path.exists(self.test_data_dir):
      os.system('rm -rf %s' % self.test_data_dir)
    self.settings_file.close()

  def test_nonexistant_dir(self):
    self.db.add_dir(self.test_data_dir)
    bad_dir = os.path.join(self.test_data_dir, 'xxx')
    self.db.sync()

  def test_add_nested_dir_doesnt_dup(self):
    self.db.add_dir(self.test_data_dir)
    sub_dir = os.path.join(self.test_data_dir, 'project1')
    self.db.add_dir(sub_dir)
    hits = self.db.search('MySubSystem.c')
    self.assertEquals(1, len(hits))
    self.assertEquals(os.path.join(self.test_data_dir, 'project1/MySubSystem.c'), hits[0])

  def test_search_unique(self):
    self.db.add_dir(self.test_data_dir)
    hits = self.db.search('MySubSystem.c')
    self.assertEquals(1, len(hits))
    self.assertEquals(os.path.join(self.test_data_dir, 'project1/MySubSystem.c'), hits[0])

  def test_partial_search(self):
    self.db.add_dir(self.test_data_dir)
    hits = self.db.search('MyClass')
    self.assertTrue(len(hits) >= 2)
    self.assertTrue(os.path.join(self.test_data_dir, 'project1/MyClass.c') in hits)
    self.assertTrue(os.path.join(self.test_data_dir, 'project1/MyClass.h') in hits)

  def test_dir_symlinks_dont_dup(self):
    self.db.add_dir(self.test_data_dir)

  def test_search_more_than_max(self):
    # find something where you get more than a sane number of requests
    pass

  def test_add_file_after_scan(self):
    # not implemented
    pass

