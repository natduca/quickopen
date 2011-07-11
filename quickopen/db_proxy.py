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

class DBDirProxy(object):
  def __init__(self, obj):
    self.path = obj.path
    self.id = obj.id

class DBProxy(object):
  def __init__(self, host, port, start_if_needed = False):
    if start_if_needed:
      raise Exception("Not implemented")
    self.conn_ = httplib.HTTPConnection(host, port, True)

  def _req(self, method, path, data):
    if data:
      data = json.dumps(data)
    self.conn.request(method, path, data)
    res = self.conn.getresponse()
    self.assertEquals(res.status, 200)
    res = json.loads(res.read())
    return res

  @property
  def dirs(self):
    ret = self._req('GET', '/dirs')
    assert ret.status == 'OK'
    return map(lambda x: DBDirProxy(x.id, x.path), ret.dirs)

  def add_dir(self, d):
    ret = self._req('POST', '/dirs/new', d)
    assert ret.status == 'OK'
    self._dirs = None
    return ret.dir_id

  def del_dir(self, d):
    if type(d) != DBDirProxy:
      raise Exception("Expected DBDirProxy")
    ret = self._req('POST', '/dirs/%s', d.id)
    assert ret.status == 'OK'
