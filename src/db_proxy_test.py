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
import subprocess
import tempfile
import time

def is_port_available(port):
  import socket
  s = socket.socket()
  try:
    s.connect(('localhost', port))
  except socket.error:
    return True
  s.close()
  return False

TEST_PORT=12345

# Import should fail if a daemon is running
if not is_port_available(TEST_PORT):
  raise Exception("DaemonRunning")

class DBProxyTest(db_test_base.DBTestBase, unittest.TestCase):
  def setUp(self):
    db_test_base.DBTestBase.setUp(self)
    self.settings_file = tempfile.NamedTemporaryFile()
    self.proc = subprocess.Popen(['./quickopend', '--settings', self.settings_file.name, '--port', str(TEST_PORT), '--test'])
    time.sleep(0.2) # let it come up...
    self.db = db_proxy.DBProxy('localhost', TEST_PORT)

  def tearDown(self):
    self.proc.kill()
    self.settings_file.close()
    db_test_base.DBTestBase.tearDown(self)
