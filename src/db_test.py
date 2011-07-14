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

  def tearDown(self):
    DBTestBase.tearDown(self)
    self.settings_file.close()

