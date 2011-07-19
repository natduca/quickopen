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
import subprocess
import time
import json

from dyn_object import DynObject
from event import Event

class DBDirProxy(object):
  def __init__(self, id, path):
    self.id = id
    self.path = path

class DBProxy(object):
  def __init__(self, host, port, start_if_needed = False, port_for_autostart=-1):
    if start_if_needed and port_for_autostart == -1:
      raise Exception("Cannot start_if_needed without a port_for_autostart")
    self.host = host
    self.port = port
    self._start_if_needed = start_if_needed
    if self._start_if_needed:
      self._port_for_autostart = port_for_autostart
      self.couldnt_start_daemon = Event()
    self.conn = httplib.HTTPConnection(host, port, True)
    self._dir_lut = {}

  def try_to_start_quickopend(self):
    args = ['./quickopend']
    print 'No quickopend running. Launching it...'
    self.proc = subprocess.Popen(args)
    

    print 'Making sure it came up on port %i' % self._port_for_autostart
    ok = False
    for i in range(10):
      try:
        conn = httplib.HTTPConnection('localhost', self._port_for_autostart, True)
        conn.request('GET', '/ping')
      except:
        time.sleep(0.05)
        continue

      res = conn.getresponse()
      if res.status != 200:
        ok = False
        break
      if json.loads(res.read()) != 'pong':
        ok = False
        break
      ok = True
      break
    if not ok:
      self.couldnt_start_daemon.fire()
      raise Exception("Daemon did not come up")
    

  def _req(self, method, path, data = None):
    if data:
      if type(data) == DynObject:
        data = data.as_json()
      else:
        data = json.dumps(data)
    try:
      self.conn.request(method, path, data)
    except httplib.CannotSendRequest:
      if self._start_if_needed:
        self.try_to_start_quickopend()
        self._start_if_needed = False # dont do it twice
      self.conn = httplib.HTTPConnection(self.host, self.port, True)
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
    return self.sync_status().is_syncd

  def sync(self):
    ret = self._req('POST', '/sync')

  def sync_status(self):
    return self._req('GET', '/sync_status')

