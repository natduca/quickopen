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
from dyn_object import *
import json
import logging
import re
import sys
import traceback
import urlparse
import BaseHTTPServer

from db import DB

"""
Exception that you can throw in a handler that will trigger a 404 response.
"""
class NotFoundException(Exception):
  def __init__(self,*args):
    Exception.__init__(self, *args)

"""
Exception that you can throw in a handler that will not get logged, but 
that will trigger a 500 response.
"""
class SilentException(Exception):
  def __init__(self,*args):
    Exception.__init__(self, *args)

class _RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def __init__(self, request, client_address, server):
    BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)
    self.server = server

  @property
  def db(self):
    return self.server.db

  def send_json(self, obj):
    if type(obj) == DynObject:
      text = obj.as_json()
    else:
      text = json.dumps(obj)
    self.send_response(200, 'OK')
    self.send_header('Cache-Control', 'no-cache')
    self.send_header('Content-Type', 'applicaiton/json')
    self.send_header('Content-Length', len(text))
    self.end_headers()
    self.wfile.write(text)

  def send_result(self, route, obj):
    if route.output == 'json':
      self.send_json(obj)
    else:
      raise Exception('Unrecognized output type: ' + route.output)

  def log_message(self, format, *args):
    logging.info(format, args)

  def handleRequest(self, verb):
    path = urlparse.urlsplit(self.path)[2]

    if 'Content-Length' in self.headers:
      cl = int(self.headers['Content-Length'])
      text = self.rfile.read(cl).encode('utf8')
      obj = DynObject.loads(text)
    else:
      obj = None

    if path == '/ping':
      self.send_json('pong')
      return

    (route,verb_ok,match) = self.server.find_route_matching(path, verb)
    if route:
      if verb_ok:
        try:
          resp = route.handler(match, verb, obj)
          self.send_result(route, resp)
        except Exception, ex:
          if not isinstance(ex,SilentException):
            traceback.print_exc()
          if isinstance(ex,NotFoundException):
            self.send_response(404, 'NotFound')
          else:
            self.send_response(500, 'Exception in handler')
          self.send_header('Content-Length', 0)
          self.end_headers()
      else:
        self.send_response(405, 'Method Not Allowed')
        self.send_header('Content-Length', 0)
        self.end_headers()
    else:
      self.send_response(404, 'Not Found')
      self.send_header('Content-Length', 0)
      self.end_headers()

  def do_GET(self):
    self.handleRequest('GET')

  def do_DELETE(self):
    self.handleRequest('DELETE')

  def do_POST(self):
    self.handleRequest('POST')

class Route(object):
  def __init__(self, path_regex, output, handler, allowed_verbs):
    self.allowed_verbs = set(allowed_verbs)
    self.path_regex = path_regex
    self.output = output
    self.handler = handler

class Daemon(BaseHTTPServer.HTTPServer):
  def __init__(self, db, test_mode, *args):
    BaseHTTPServer.HTTPServer.__init__(self, *args)
    self.port_ = args[0][1]
    self.db_ = db
    self.routes = []
    self.db_.on_bound_to_server(self)
    self.test_mode = test_mode
    if test_mode:
      self.add_json_route('/exit', self.on_exit, ['POST', 'GET'])
      import daemon_test
      daemon_test.add_test_handlers_to_daemon(self)

  def on_exit(self, m, verb, data):
    logging.info("Exiting upon request.")
    self.shutdown()

  def add_json_route(self, path_regex, handler, allowed_verbs):
    re.compile(path_regex)
    self.routes.append(Route(path_regex, 'json', handler, allowed_verbs))

  def find_route_matching(self, path, verb):
    found_route = None

    for r in self.routes:
      m = re.match(r.path_regex, path)
      if m:
        found_route = r
        if verb in r.allowed_verbs:
          return (r, True, m)
    if found_route:
      return (r, False, m)
    return (None, None, None)

  def serve_forever(self):
    self.is_running_ = True
    while self.is_running_:
      self.handle_request()

  def shutdown(self):
    self.is_running_ = False
    return 1

  def run(self):
    if self.test_mode:
      logging.info('Starting quickopen daemon on port %d', self.port_)
    else:
      print 'Starting quickopen daemon on port %d' % self.port_
    self.serve_forever()
    logging.info('Shutting down quickopen daemon on port %d', self.port_)

def create(db, host, port, test_mode):
  return Daemon(db, test_mode, (host,port), _RequestHandler)

