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
import httplib
import subprocess
import tempfile
import unittest
import time
import json

TEST_PORT=12345

class DaemonTest(unittest.TestCase):
  def setUp(self):
    self.settings_file_ = tempfile.NamedTemporaryFile()
    self.proc_ = subprocess.Popen(['./quickopend', '--settings', self.settings_file_.name, '--port', str(TEST_PORT)])
    time.sleep(0.1) # let it come up...

  def test_responding(self):
    conn = httplib.HTTPConnection('localhost', TEST_PORT, True)
    conn.request('GET', '/test')
    res = conn.getresponse()
    self.assertEquals(res.status, 200)
    self.assertEquals(json.loads(res.read()), 'OK')
    print res.read()
    conn.close()

  def test_illegal(self):
    conn = httplib.HTTPConnection('localhost', TEST_PORT, True)
    conn.request('GET', '/xxx')
    res = conn.getresponse()
    self.assertEquals(res.status, 404)
    conn.close()

  def tearDown(self):
    self.proc_.kill()
    self.settings_file_.close()
