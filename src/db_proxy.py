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
import httplib
from dyn_object import *

class DBDirProxy(object):
  def __init__(self, id, path):
    self.id = id
    self.path = path

class DBProxy(object):
  def __init__(self, host, port, start_if_needed = False):
    if start_if_needed:
      raise Exception("Not implemented")
    self.conn = httplib.HTTPConnection(host, port, True)
    self._dir_lut = {}

  def _req(self, method, path, data = None):
    if data:
      if type(data) == DynObject:
        data = data.as_json()
      else:
        data = json.dumps(data)
    self.conn.request(method, path, data)
    res = self.conn.getresponse()
    if res.status != 200:
      raise Exception("On %s, got %s" % (path, res.status))
    res = DynObject.loads(res.read().encode('utf8'))
    return res

  def _get_dir(self, id, path):
    if id not in self._dir_lut:
      self._dir_lut[id] = DBDirProxy(id, path)
    assert self._dir_lut[id].path== path
    return self._dir_lut[id]
    
  @property
  def dirs(self):
    ret = self._req('GET', '/dirs')
    return map(lambda x: self._get_dir(x["id"], x["path"]), ret)

  def add_dir(self, d):
    ret = self._req('POST', '/dirs/add', {"path": d})
    assert ret.status == 'OK'
    return self._get_dir(ret.id, d)

  def delete_dir(self, d):
    if type(d) != DBDirProxy:
      raise Exception("Expected DBDirProxy")
    ret = self._req('DELETE', '/dirs/%s' % d.id)
    assert ret.status == 'OK'

  @property
  def ignores(self):
    return self._req('GET', '/ignores')

  def ignore(self, i):
    ret = self._req('POST', '/ignores/add', i)

  def unignore(self, i):
    try:
      ret = self._req('POST', '/ignores/remove', i)
    except:
      raise "Pattern not found"

  def search(self, q):
    try:
      ret = self._req('POST', '/search', q)
    except Exception:
      raise db.NotSyncdException()
    return ret

  @property
  def is_syncd(self):
    return  self._req('GET', '/sync_status').is_syncd

  def sync(self):
    ret = self._req('POST', '/sync')

  def sync_status(self):
    ret = self._req('GET', '/sync_status')
