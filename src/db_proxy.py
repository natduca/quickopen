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
import httplib
import os
import socket
import subprocess
import sys
import time
import json
import urllib
import urlparse

from db_status import DBStatus
from search_result import SearchResult
from event import Event
from trace_event import *

class DBDirProxy(object):
  def __init__(self, id, path):
    self.id = id
    self.path = path

  def __repr__(self):
    return "DBDirProxy(%s, %s)" % (self.id, self.path)

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
    args = ['./quickopend', 'run']
    sys.stderr.write('No quickopend running. Launching it...\n')
    self.proc = subprocess.Popen(args)

    sys.stderr.write('Making sure it came up on port %i\n' % self._port_for_autostart)
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
    if data != None:
      data = json.dumps(data)
    try:
      self.conn.request(method, path, data)
    except httplib.CannotSendRequest:
      self.conn = None
    except socket.error:
      self.conn = None
    if not self.conn:
      if self._start_if_needed:
        self.try_to_start_quickopend()
        self._start_if_needed = False # dont try to autostart again
      self.conn = httplib.HTTPConnection(self.host, self.port, True)
      self.conn.request(method, path, data)
    else:
      self._start_if_needed = False # if a request succeds, dont trigger autostart
    res = self.conn.getresponse()
    if res.status == 500:
      info = json.loads(res.read())
      # try to recreate the server-side exception
      try:
        module = __import__(info["module"], {}, {}, True)
        constructor = getattr(module, info["class"])
        ex = constructor(*info["args"])
      except:
        raise Exception("Server side exception: %s" % info["exception"])
      raise ex

    elif res.status != 200:
      raise Exception("On %s, got %s" % (path, res.status))
    res = json.loads(res.read().encode('utf8'))
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
    assert ret["status"] == 'OK'
    return self._get_dir(ret["id"], d)

  def delete_dir(self, d):
    if type(d) != DBDirProxy:
      raise Exception("Expected DBDirProxy")
    ret = self._req('DELETE', '/dirs/%s' % d.id)
    assert ret["status"] == 'OK'

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

  @tracedmethod
  def search(self, q, max_hits = -1, exact_match = False, current_filename = None, open_filenames = []):
    options = {}
    if max_hits != -1:
      options["max_hits"] = max_hits
    if exact_match:
      options["exact_match"] = True
    if current_filename:
      options["current_filename"] = current_filename
    q = {"query" : q,
         "open_filenames": open_filenames}
    if len(options):
      d = self._req('POST', '/search?%s' % urllib.urlencode(options), q)
    else:
      d = self._req('POST', '/search', q)
    return SearchResult.from_dict(d)

  def search_async(self, q, max_hits = -1, exact_match = False, current_filename = None, open_filenames = []):
    return AsyncSearch(self.host, self.port, q, max_hits, exact_match, current_filename, open_filenames)

  @property
  def is_up_to_date(self):
    return self.status().is_up_to_date

  @property
  def has_index(self):
    return self.status().has_index

  @tracedmethod
  def sync(self):
    ret = self._req('POST', '/sync')

  @tracedmethod
  def status(self):
    try:
      d = self._req('GET', '/status')
      return DBStatus.from_dict(d)
    except IOError:
      return DBStatus.not_running()

  def begin_reindex(self):
    return self._req('POST', '/begin_reindex')


class AsyncSearchError(object): 
  pass

class AsyncSearch(object):
  def __init__(self, host, port, q, max_hits = -1, exact_match = False, current_filename = None, open_filenames = []):
    self.async_conn = async_http_connection.AsyncHTTPConnection(host, port)

    options = {}
    if max_hits != -1:
      options["max_hits"] = max_hits
    if exact_match:
      options["exact_match"] = True
    if current_filename:
      options["current_filename"] = current_filename
    q = {"query" : q,
         "open_filenames": open_filenames}
    if len(options):
      self.async_conn.begin_request('POST', '/search?%s' % urllib.urlencode(options), json.dumps(q))
    else:
      self.async_conn.begin_request('POST', '/search', json.dumps(q))
    self._result = None

  @property
  def ready(self):
     return self.async_conn.is_response_ready()

  @property
  def result(self):
     if not self.async_conn:
       raise AsyncSearchError, 'connection died during search'

     if not self._result:
       res = self.async_conn.get_response()
       if res.status != 200:
         self.async_conn.close()
         self.async_conn = None
         raise AsyncSearchError, 'got status %i' % res.status
       else:
         data = res.read()
         res = json.loads(data.encode('utf8'))
         self._result = SearchResult.from_dict(res)
     return self._result
