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
import time
import unittest
from dir_cache import DirCache
from test_data import TestData

class DirCacheTest(unittest.TestCase):
  def setUp(self):
    self.test_data = TestData()

  def tearDown(self):
    self.test_data.close()

  def test_listdir_on_invalid_dir(self):
    c = DirCache()
    # shoudl not raise exception
    c.listdir(self.test_data.path_to('xxx'))

  def test_listdir_when_gone(self):
    c = DirCache()
    something = self.test_data.path_to('something');
    c.listdir(something)
    self.test_data.rm_rf(something)
    self.assertEquals([], c.listdir(self.test_data.path_to('something')))

  def test_up_to_date_after_change(self):
    c = DirCache()
    something = self.test_data.path_to('something');
    c.listdir(something)
    self.test_data.rm_rf(something)
    self.assertEquals([], c.listdir(self.test_data.path_to('something')))

  def test_toplevel_deletion_causes_changed(self):
    c = DirCache()
    base = self.test_data.path_to('');
    something = self.test_data.path_to('something');
    c.listdir(base)
    c.listdir(something)
    self.assertFalse(c.listdir_with_changed_status(base)[1])
    self.assertFalse(c.listdir_with_changed_status(something)[1])
    time.sleep(1.2)
    self.test_data.rm_rf(something)
    self.assertTrue(c.listdir_with_changed_status(base)[1])
    self.assertTrue(c.listdir_with_changed_status(something)[1])

  def test_toplevel_addition_causes_change(self):
    c = DirCache()
    base = self.test_data.path_to('');
    c.listdir(base)
    self.assertFalse(c.listdir_with_changed_status(base)[1])
    time.sleep(1.2)
    self.test_data.write1('READMEx')
    self.assertTrue(c.listdir_with_changed_status(base)[1])

  def test_toplevel_modification_doesnt_cause_change(self):
    c = DirCache()
    base = self.test_data.path_to('');
    c.listdir(base)
    self.assertFalse(c.listdir_with_changed_status(base)[1])
    time.sleep(1.2)
    self.test_data.write1('READMEx')
    self.assertTrue(c.listdir_with_changed_status(base)[1])
    time.sleep(1.2)
    self.test_data.write2('READMEx')
    self.assertFalse(c.listdir_with_changed_status(base)[1])


