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
import select
import time
import socket
import sys
import json

from trace_event import *

class AsyncError(Exception):
  pass

class RequestPending(Exception):
  pass

class RequestNotPending(Exception):
  pass

IDLE = 'idle'
REQUEST_PENDING = 'request_pending'
SOCKET_READABLE = 'socket_readable'

class AsyncHTTPConnection(object):
  def __init__(self, host, port):
    self.conn = httplib.HTTPConnection(host, port)
    self.state = IDLE

  @trace
  def connect(self):
    if not self.conn.sock:
      try:
        self.conn.connect()
      except socket.error:
        print 'died during connect'
        raise AsyncError()

  @trace
  def begin_request(self, method, url, data = None):
    if self.state != IDLE:
      raise RequestPending()
    self.connect()
    if not data:
      data = ''
    try:
      self.conn.putrequest(method, url)
      self.conn.putheader('Content-Length', len(data))
      self.conn.putheader('Connection', 'keep-alive')
      self.conn.endheaders()
      if len(data):
        self.conn.send(data)
      self.state = REQUEST_PENDING
    except httplib.CannotSendRequest:
      self.conn.close()
      print 'died during begin_request'
      raise AsyncError()

  @trace
  def is_response_ready(self, timeout = 0):
    if self.state == IDLE:
      raise RequestNotPending()
    if self.state == SOCKET_READABLE:
      return True
    if not self.conn.sock:
      self.state = SOCKET_READABLE
      return True
    r,w,x = select.select([self.conn.sock.fileno(),], [], [], timeout)
    if len(r):
      self.state = SOCKET_READABLE
      return True
    else:
      return False


  @trace
  def get_response(self):
    if self.state == REQUEST_PENDING:
      raise RequestPending()
    if self.state == IDLE:
      raise RequestNotPending()
    if not self.conn.sock:
      raise AsyncError()
    # todo, make sure we got a readable
    try:
      r = self.conn.getresponse()
      return r
    except httplib.BadStateLine:
      print "lost during get response"
      r = None
      self.state = IDLE
      self.conn.close()
