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
from __future__ import absolute_import

import daemon as python_daemon
import httplib
import json
import logging
import sys
import optparse
import os
import re
import time
import src.daemon
import src.default_port
import src.db_stub
import src.settings
import src.prelaunchd

from trace_event import *

class ForegroundDaemonContext:
  def __enter__(self):
    pass
  def __exit__(self, exec_type, exec_value, traceback):
    pass

def is_port_listening(host, port):
  import socket
  s = socket.socket()
  try:
    s.connect((host, port))
  except socket.error:
    return False
  s.close()
  return True

def flush_trace_event(daemon):
  trace_flush()
  daemon.add_delayed_task(flush_trace_event, 5, daemon)

def CMDrun(parser):
  """Runs the quickopen daemon"""
  (options, args) = parser.parse_args()
  if is_port_listening(options.host, options.port):
    print "%s:%s in use. Try 'quickopend stop' first?" % (options.host, options.port)
    return 255
  prelaunchdaemon = None

  if options.test:
    logging.info('Starting quickopen daemon on port %d', options.port)
  else:
    print 'Starting quickopen daemon on port %d' % options.port

  try:
    # Tests assume that quickopend created in the foreground
    if options.test or options.foreground:
      context = ForegroundDaemonContext()
    else:
      context = python_daemon.DaemonContext()

    with context:
      service = src.daemon.create(options.host, options.port, options.test)
      if trace_is_enabled():
        service.add_delayed_task(flush_trace_event, 5, service)
      db_stub = src.db_stub.DBStub(options.settings, service)
      prelaunchd = src.prelaunchd.PrelaunchDaemon(service)

      service.run()
  finally:
    if prelaunchdaemon:
      prelaunchdaemon.stop()

  logging.info('Shutting down quickopen daemon on port %d', options.port)

  return 0


def CMDstatus(parser):
  """Gets the status of the quickopen daemon"""
  (options, args) = parser.parse_args()
  if not is_port_listening(options.host, options.port):
    print "Not running"
    return 255

  try:
    conn = httplib.HTTPConnection(options.host, options.port, True)
    conn.request('GET', '/status')
    resp = conn.getresponse()
  except:
    print "Not responding"
    return 255

  if resp.status != 200:
    print "Service running on %s:%i is probaby not quickopend" % (options.host, options.port)
    return 255

  status_str = resp.read()
  status = json.loads(status_str)
  print status["status"]
  return 0

def CMDstop(parser):
  """Gets the status of the quickopen daemon"""
  (options, args) = parser.parse_args()
  try:
    conn = httplib.HTTPConnection(options.host, options.port, True)
    conn.request('GET', '/exit')
    resp = conn.getresponse()
  except:
    print "Not responding"
    return 255

  if resp.status != 200:
    print "Service running on %s:%i is probaby not quickopend" % (options.host, options.port)
    return 255

  status_str = resp.read()
  status = json.loads(status_str)
  if status["status"] != "OK":
    print "Stop failed with unexpected result %s" % status["status"]
    return 255
  print "Existing quickopend on %s:%i stopped" % (options.host, options.port)
  return 0

def CMDrestart(parser):
  """Restarts the quickopen daemon"""
  (options, args) = parser.parse_args()

  ret = CMDstop(parser)
  if ret != 0:
    return ret
  time.sleep(0.25)

  tries = 0
  while is_port_listening(options.host, options.port) and tries < 10:
    tries += 1
    time.sleep(0.1)
  if tries == 10:
    print "Previous quickopend did not stop."
    return 255
  CMDrun(parser)
  return 0

# Subcommand addins to optparse, taken from git-cl.py,
# http://src.chromium.org/svn/trunk/tools/depot_tools/git_cl.py
###########################################################################

def Command(name):
  return getattr(sys.modules[__name__], 'CMD' + name, None)


def CMDhelp(parser):
  """print list of commands or help for a specific command"""
  _, args = parser.parse_args()
  if len(args) == 1:
    return main(args + ['--help'])
  parser.print_help()
  return 0


def GenUsage(parser, command):
  """Modify an OptParse object with the function's documentation."""
  obj = Command(command)
  more = getattr(obj, 'usage_more', '')
  if command == 'help':
    command = '<command>'
  else:
    # OptParser.description prefer nicely non-formatted strings.
    parser.description = re.sub('[\r\n ]{2,}', ' ', obj.__doc__)
  parser.set_usage('usage: %%prog %s [options] %s' % (command, more))

def getdoc(x):
  if getattr(x, '__doc__'):
    return x.__doc__
  return '<Missing docstring>'

def main_usage():
  return "Usage: quickopend [global options] <command> [command arguments]"

def main(parser):
  """Doesn't parse the arguments here, just find the right subcommand to
  execute."""

  # Do it late so all commands are listed.
  CMDhelp.usage_more = ('\n\nCommands are:\n' + '\n'.join([
      '  %-10s %s' % (fn[3:], Command(fn[3:]).__doc__.split('\n')[0].strip())
      for fn in dir(sys.modules[__name__]) if fn.startswith('CMD')]))
  parser.add_option('--host', dest='host', action='store', help='Hostname to listen on')
  parser.add_option('--port', dest='port', action='store', help='Port to run on')
  parser.add_option('--settings', dest='settings', action='store', default='~/.quickopend', help='Settings file to use')
  parser.add_option('--test', dest='test', action='store_true', default=False, help='Adds test hooks')
  parser.add_option('--trace', dest='trace', action='store_true', default=False, help='Records performance tracing information to quickopen.trace')
  parser.add_option('--foreground', dest='foreground', action='store_true', default=False, help='Starts quickopend in the foreground instead of forking')
  old_parser_args = parser.parse_args
  def parse():
    options, args = old_parser_args()
    if options.trace:
      trace_enable("./%s.trace" % "quickopen")
    settings_file = os.path.expanduser(options.settings)
    settings = src.settings.Settings(settings_file)
    settings.register('host', str, 'localhost')
    settings.register('port', int, src.default_port.get())
    options.settings = settings

    if not options.port:
      options.port = settings.port
    else:
      options.port = int(options.port)

    if not options.host:
      options.host = settings.host

    return options, args
  parser.parse_args = parse

  non_switch_args = [i for i in sys.argv[1:] if not i.startswith('-')]
  if non_switch_args:
    command = Command(non_switch_args[0])
    if command:
      if non_switch_args[0] == 'help':
        CMDhelp.usage_more = ('\n\nCommands are:\n' + '\n'.join([
              '  %-10s %s' % (fn[3:], getdoc(Command(fn[3:])).split('\n')[0].strip())
              for fn in dir(sys.modules[__name__]) if fn.startswith('CMD')]))

      # "fix" the usage and the description now that we know the subcommand.
      GenUsage(parser, non_switch_args[0])
      new_args = list(sys.argv[1:])
      new_args.remove(non_switch_args[0])
      new_args.insert(0, sys.argv[0])
      sys.argv = new_args
      return command(parser)
    else:
      # Not a known command. Default to help.
      print "Unrecognized command: %s\n" % non_switch_args[0]
  else: # default command
    CMDrun.usage_more = ('\n\nCommands are:\n' + '\n'.join([
          '  %-10s %s' % (fn[3:], getdoc(Command(fn[3:])).split('\n')[0].strip())
          for fn in dir(sys.modules[__name__]) if fn.startswith('CMD')]))
    GenUsage(parser, 'run')
    return CMDrun(parser)
