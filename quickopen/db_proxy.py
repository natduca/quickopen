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

class DBProxy(object):
  def __init__(self, host, port):
    self.conn_ = httplib.HTTPConnection(host, port, True)

  def _get(self, path):
    if self.conn == None:
      self.conn = httplib.HTTPConnection('localhost', TEST_PORT, True)
    self.conn.request('GET', path)
    res = self.conn.getresponse()
    self.assertEquals(res.status, 200)
    res = json.loads(res.read())
    return res

  def _post(self, path, data):
    if self.conn == None:
      self.conn = httplib.HTTPConnection('localhost', TEST_PORT, True)
    self.conn.request('POST', path, json.dumps(data))
    res = self.conn.getresponse()
    self.assertEquals(res.status, 200)
    res = json.loads(res.read())
    return res


  def dir(self, dir):
    self.conn_.request('POST', '/dirs')
    res = conn.getresponse()
    self.assertEquals(res.status, 200)
    self.assertEquals(json.loads(res.read()), 'OK')
    conn.close()

    # POST xxx

