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
import temporary_daemon
import async_http_connection

def AsyncHTTPConnectionTest(self):
  def setUp(self):
    self.daemon = temporary_daemon.TemporaryDaemon()

  def test_basic(self):
    async_http_connection.AsyncHTTPConnection(daemon.host, daemon.port)
    async_http_connection.begin_request('GET', '/')
    while not async_http_connection.is_response_ready():
      time.sleep(0.1)
      print 'waiting...'
    res = async_http_connection.get_response()
    print res.status
    print res.read()

  def tearDown(self):
    self.daemon.close()
