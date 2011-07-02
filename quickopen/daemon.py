import json
import logging
import sys
import urlparse
import BaseHTTPServer

from db import DB

class _RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def __init__(self, request, client_address, server):
    BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)
    self.server_ = server

  @property
  def db(self):
    return self.server_.db

  def send_json(self, obj):
    text = json.dumps(obj)
    self.send_response(200, 'OK')
    self.send_header('Cache-Control', 'no-cache')
    self.send_header('Content-Type', 'applicaiton/json')
    self.send_header('Content-Length', len(text))
    self.end_headers()
    self.wfile.write(text)

  def do_GET(self):
    (_, _, path, params, query) = urlparse.urlsplit(self.path)
    if path == '/test':
      self.send_json('OK')
      return
    else:
      if path in self.server_.json_routes_:
        resp = self.server_.json_routes_[path](self)
        self.send_json(resp)
        return

    self.send_response(404, 'Illegal')
    self.send_header('Content-Length', 0)
    self.end_headers()

  def do_POST(self):
    (_, _, path, params, query, fragment) = urlparse.urlsplit(self.path)
    if path == '/add_dir':
      return

    self.send_response(404, 'Illegal')
    self.send_header('Content-Length', 0)
    self.end_headers()

class _QuittableHTTPServer(BaseHTTPServer.HTTPServer):
  def __init__(self, db, *args):
    BaseHTTPServer.HTTPServer.__init__(self, *args)
    self.port_ = args[0][1]
    self.db_ = db
    self.db_.on_bound_to_server(self)
    self.json_routes_ = dict()
  
  def add_json_route(self, path, handler):
    self.json_routes_[path] = handler

  def serve_forever(self):
    self.is_running_ = True
    while self.is_running_:
      self.handle_request()

  def shutdown(self):
    self.is_running_ = False
    return 1

  def run(self):
    logging.warning("Starting local server on port %d", self.port_)
    self.serve_forever()
    logging.warning("Shutting down local server on port %d", self.port_)

def create(db, host, port):
  return _QuittableHTTPServer(db, (host,port), _RequestHandler)

