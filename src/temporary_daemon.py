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
import db_proxy
import httplib
import json
import logging
import subprocess
import tempfile
import time

def is_port_listening(port):
  import socket
  s = socket.socket()
  try:
    s.connect(('localhost', port))
  except socket.error:
    return False
  s.close()
  return True

TEST_PORT=12345

class TemporaryDaemon(object):
  def __init__(self):
    # If a daemon is running, try killing it via /kill
    if is_port_listening(TEST_PORT):
      for i in range(2):
        logging.warn("Existing daemon found. Asking it to exit")
        try:
          conn = httplib.HTTPConnection('localhost', TEST_PORT, True)
          conn.request('GET', '/exit')
        except:
          break
        res = conn.getresponse()
        if res.status != 200:
          break
        else:
          time.sleep(0.2)

    if is_port_listening(TEST_PORT):
      raise Exception("Daemon running")

    self.daemon_settings_file = tempfile.NamedTemporaryFile()
    args = ['./quickopend', 'run', '--settings', self.daemon_settings_file.name, '--port', str(TEST_PORT)]
    args.append('--test')

    self.proc = subprocess.Popen(args)
    ok = False
    for i in range(10):
      try:
        conn = httplib.HTTPConnection('localhost', TEST_PORT, True)
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
      raise Exception("Daemon did not come up")

    self._conn = None
    self._db_proxy = None

  def close(self):
    try:
      conn = httplib.HTTPConnection('localhost', TEST_PORT, True)
      conn.request('GET', '/exit')
    except:
      pass
    self.proc.wait()
    self.daemon_settings_file.close()

  @property
  def host(self):
    return 'localhost'

  @property
  def port(self):
    return TEST_PORT

  @property
  def conn(self):
    if not self._conn:
      self._conn = httplib.HTTPConnection(self.host, self.port, True)
    return self._conn

  @property
  def db_proxy(self):
    if not self._db_proxy:
      self._db_proxy = db_proxy.DBProxy('localhost', TEST_PORT)
    return self._db_proxy
