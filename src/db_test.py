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

from db_test_base import DBTestBase

# Tests are actually in DBTestBase
class DBTest(DBTestBase, unittest.TestCase):
  def setUp(self):
    self.settings_file = tempfile.NamedTemporaryFile()
    self.settings = settings.Settings(self.settings_file.name)
    self.db = db.DB(self.settings)
    DBTestBase.setUp(self)

  def test_dir_persistence(self):
    d1 = os.path.join(self.test_data_dir, 'project1')
    self.db.add_dir(d1)
    self.db.sync()

    settings2 = settings.Settings(self.settings_file.name)
    db2 = db.DB(settings2)
    self.assertEquals([d1], map(lambda d: d.path, db2.dirs))

  def test_change_while_syncing(self):
    d1 = os.path.join(self.test_data_dir, 'project1')
    d2 = os.path.join(self.test_data_dir, 'something')
    self.db.add_dir(d1)
    self.db.step_indexer()
    self.db.add_dir(d2)
    self.db.sync()
    res = self.db.search('something_file.txt')
    self.assertEquals(1, len(res.filenames))
    self.assertEquals(os.path.join(self.test_data_dir, 'something/something_file.txt'), res.filenames[0])

  def tearDown(self):
    DBTestBase.tearDown(self)
    self.settings_file.close()
