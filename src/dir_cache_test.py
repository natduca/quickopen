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
