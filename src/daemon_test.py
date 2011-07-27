# Copyright 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import daemon as daemon_module
import httplib
import json
import temporary_daemon
import time
import unittest

from dyn_object import *

class DaemonTest(unittest.TestCase):
  def setUp(self):
    self.daemon = temporary_daemon.TemporaryDaemon()
    self.conn = self.daemon.conn

  # basics
  def test_responding(self):
    self.conn.request('GET', '/ping')
    res = self.conn.getresponse()
    self.assertEquals(res.status, 200)
    self.assertEquals(json.loads(res.read()), 'pong')

  def test_missing(self):
    self.conn.request('GET', '/xxx')
    res = self.conn.getresponse()
    self.assertEquals(res.status, 404)

  # GET requests via handlers
  def get_json(self, path):
    self.conn.request('GET', path)
    res = self.conn.getresponse()
    self.assertEquals(res.status, 200)
    res = json.loads(res.read())
    return res

  def post_json(self, path, data):
    self.conn.request('POST', path, json.dumps(data))
    res = self.conn.getresponse()
    self.assertEquals(res.status, 200)
    res = json.loads(res.read())
    return res

  def test_simple_handler(self):
    self.assertEquals(self.get_json('/test_simple'), 'simple_ok')
    self.assertEquals(self.post_json('/test_simple', 'simple_ok'), 'simple_ok')

  def test_invalid_verb_on_simple(self):
    self.conn.request('DELETE', '/test_simple')
    res = self.conn.getresponse()
    self.assertEquals(res.status, 405)

  def test_complex_handler(self):
    self.assertEquals(self.get_json('/test_complex/2'), 2)
    self.assertEquals(self.post_json('/test_complex/2', 'complex_ok'), 2)

  def test_handler_with_exception_handler(self):
    self.conn.request('GET', '/test_server_exception')
    res = self.conn.getresponse()
    self.assertEquals(res.status, 500)

    self.conn.request('POST', '/test_server_exception')
    res = self.conn.getresponse()
    self.assertEquals(res.status, 500)

  def test_delete(self):
    self.conn.request('DELETE', '/test_delete')
    res = self.conn.getresponse()
    self.assertEquals(res.status, 200)
    self.assertEquals(json.loads(res.read()), 'OK')

  def test_dyn_obj(self):
    self.conn.request('GET', '/test_dyn_obj')
    res = self.conn.getresponse()
    self.assertEquals(res.status, 200)
    x = DynObject.loads(res.read())
    self.assertEquals(x.status, 'OK')

  def tearDown(self):
    if self.conn:
      self.conn.close()
    self.daemon.close()


def add_test_handlers_to_daemon(daemon):
  def handler_for_simple(m, verb, data = None):
    if verb == 'POST':
      assert data == 'simple_ok'
    return 'simple_ok'
  daemon.add_json_route('/test_simple', handler_for_simple, ['GET','POST'])

  def handler_for_complex(m, verb, data = None):
    if verb == 'POST':
      assert data == 'complex_ok'
    assert int(m.group(1)) == 2
    return 2
  daemon.add_json_route('/test_complex/(\d+)', handler_for_complex, ['GET', 'POST'])

  def handler_for_server_exception(m, verb, data = None):
    raise daemon_module.SilentException('Server side error')
  daemon.add_json_route('/test_server_exception', handler_for_server_exception, ['GET', 'POST'])

  def handler_for_delete(m, verb, data = None):
    assert verb == 'DELETE'
    return 'OK'
  daemon.add_json_route('/test_delete', handler_for_delete, ['DELETE'])

  def handler_for_dynobj(m, verb, data):
    x = DynObject()
    x.status = 'OK'
    return x
  daemon.add_json_route('/test_dyn_obj', handler_for_dynobj, ['GET'])


  def handler_for_sleep(m, verb, data):
    import time
    time.sleep(0.25)
    return 'OK'
  daemon.add_json_route('/sleep', handler_for_sleep, ['GET'])
