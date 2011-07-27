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
import async_http_connection
import temporary_daemon
import unittest
import time
class AsyncHTTPConnectionTest(unittest.TestCase):
  def setUp(self):
    self.daemon = temporary_daemon.TemporaryDaemon()

  def test_basic(self):
    conn = async_http_connection.AsyncHTTPConnection(self.daemon.host, self.daemon.port)
    conn.begin_request('GET', '/sleep')
    while not conn.is_response_ready():
      time.sleep(0.0001)
    res = conn.get_response()
    text = res.read()
    self.assertEquals(text, '"OK"')

  def tearDown(self):
    self.daemon.close()
