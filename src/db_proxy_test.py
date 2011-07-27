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
import db_proxy
import db_test_base
import os
import subprocess
import tempfile
import temporary_daemon
import time

class DBProxyTest(db_test_base.DBTestBase, unittest.TestCase):
  def setUp(self):
    db_test_base.DBTestBase.setUp(self)
    self.daemon = temporary_daemon.TemporaryDaemon()
    self.db = self.daemon.db_proxy

  def test_search_async(self):
    self.db.add_dir(self.test_data_dir)
    self.assertEquals(False, self.db.is_syncd)
    self.db.sync()

    a = self.db.search_async('MySubSystem.c')
    while not a.ready:
      time.sleep(0.25)
    res = a.result

    self.assertEquals(1, len(res.hits))
    self.assertEquals(os.path.join(self.test_data_dir, 'project1/MySubSystem.c'), res.hits[0])
    
  def tearDown(self):
    self.daemon.close()
    db_test_base.DBTestBase.tearDown(self)
