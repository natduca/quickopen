import json
import logging
import re
import sys
import traceback
import urlparse
import BaseHTTPServer

from db import DB

class _RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def __init__(self, request, client_address, server):
    BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)
    self.server = server

  @property
  def db(self):
    return self.server.db

  def send_json(self, obj):
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

  def do_GET(self):
    path = urlparse.urlsplit(self.path)[2]
    if path == '/ping':
      self.send_json('pong')
      return
    route = self.server.find_route_matching(path, 'GET')
    if route:
      try:
        resp = route.handler(self, 'GET')
        self.send_result(route, resp)
      except:
        traceback.print_exc()
        self.send_response(500, 'Exception in handler')
        self.send_header('Content-Length', 0)
        self.end_headers()
      return
    else:
      self.send_response(404, 'Illegal')
      self.send_header('Content-Length', 0)
      self.end_headers()

  def do_DELETE(self):
    path = urlparse.urlsplit(self.path)[2]
    route = self.server.find_route_matching(path, 'DELETE')
    if route:
      try:
        resp = route.handler(self, 'DELETE')
        self.send_result(route, resp)
      except:
        traceback.print_exc()
        self.send_response(500, 'Exception in handler')
        self.send_header('Content-Length', 0)
        self.end_headers()
      return
    else:
      self.send_response(404, 'Illegal')
      self.send_header('Content-Length', 0)
      self.end_headers()

  def do_POST(self):
    path = urlparse.urlsplit(self.path)[2]
    route = self.server.find_route_matching(path, 'GET')
    if route:
      if 'Content-Length' in self.headers:
        cl = int(self.headers['Content-Length'])
        text = self.rfile.read(cl)
        obj = json.loads(text)
      else:
        obj = None

      try:
        resp = route.handler(self, 'POST', obj)
        self.send_result(route, resp)
      except:
        traceback.print_exc()
        self.send_response(500, 'Exception in handler')
        self.send_header('Content-Length', 0)
        self.end_headers()
      return

    self.send_response(404, 'Illegal')
    self.send_header('Content-Length', 0)
    self.end_headers()

class Route(object):
  def __init__(self, path_regex, output, handler, allowed_verbs):
    self.allowed_verbs = set(allowed_verbs)
    self.path_regex = path_regex
    self.output = output
    self.handler = handler

class Daemon(BaseHTTPServer.HTTPServer):
  def __init__(self, db, test, *args):
    BaseHTTPServer.HTTPServer.__init__(self, *args)
    self.port_ = args[0][1]
    self.db_ = db
    self.routes = []
    self.db_.on_bound_to_server(self)
    if test:
      import daemon_test
      daemon_test.add_test_handlers_to_daemon(self)

  def add_json_route(self, path_regex, handler, allowed_verbs):
    self.routes.append(Route(path_regex, 'json', handler, allowed_verbs))

  def find_route_matching(self, path, verb):
    for r in self.routes:
      if verb in r.allowed_verbs and re.match(r.path_regex, path):
        return r
    return None

  def serve_forever(self):
    self.is_running_ = True
    while self.is_running_:
      self.handle_request()

  def shutdown(self):
    self.is_running_ = False
    return 1

  def run(self):
    logging.warning("Starting quickopen daemon on port %d", self.port_)
    self.serve_forever()
    logging.warning("Shutting down quickopen daemon on port %d", self.port_)

def create(db, host, port, test):
  return Daemon(db, test, (host,port), _RequestHandler)

