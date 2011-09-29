#!/usr/bin/python2.6
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
import logging
import optparse
import os
import platform
import prelaunch
import re
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../third_party/py_trace_event/"))
try:
  from trace_event import *
except:
  print "Could not find py_trace_event. Did you forget 'git submodule update --init'"
  sys.exit(255)

import src.settings
import src.db_proxy

###########################################################################

def CMDadd(parser, args):
  """Adds a directory to the index"""
  (options, args) = parser.parse_args(args)
  settings = load_settings(options)
  db = open_db(options)
  if len(args) == 0:
    parser.error('Expected at least one directory')
  for d in args:
    db.add_dir(d)
  return 0

def CMDdirs(parser, args):
  """Lists currently-indexed directories"""
  (options, args) = parser.parse_args(args)
  settings = load_settings(options)
  db = open_db(options)
  if len(args):
    parser.error('Unrecognized args: %s' % ' '.join(args))
  print "\n".join([x.path for x in db.dirs])
  return 0

def CMDrmdir(parser, args):
  """Removes a currently-indexed directory"""
  (options, args) = parser.parse_args(args)
  settings = load_settings(options)
  db = open_db(options)
  dmap = {}
  for d in db.dirs:
    dmap[d.path] = d
  ok = True
  for d in args:
    if d not in dmap:
      ok = False
      print "%s not found" % d
    else:
      db.delete_dir(dmap[d])
      print "%s removed" % d
  if ok:
    return 0
  return 255

def CMDsearch(parser, args):
  """Search for a file"""
  parser.add_option('--ok', dest='ok', action='store_true', default=False, help='Output "OK" before results')
  (options, args) = parser.parse_args(args)
  settings = load_settings(options)
  if not trace_is_enabled() and settings.trace:
    trace_enable("%s.trace" % sys.argv[0])
  db = open_db(options)

  def run():
    # try using gtk
    has_gtk = False
    try:
      import pygtk
      pygtk.require('2.0')
      has_gtk = True
    except ImportError:
      pass

    if has_gtk:
      import src.open_dialog_gtk
      return src.open_dialog_gtk.run(settings, db)

    # if that didn't work, try using wx
    has_wx = False
    try:
      import wx
      has_wx = True
    except ImportError:
      pass

    if has_wx:
      import src.open_dialog_wx
      return src.open_dialog_wx.run(settings, db)

    raise ImportError()
  
  try:
    res = run()
  except ImportError:
    print "pygtk nor WxPython found. Please install one and try again.\n"
    return 255

  if res:
    if options.ok:
      print "OK"
    print "\n".join(res)
    return 0

def CMDstatus(parser, args):
  """Checks the status of the quick open database"""
  (options, args) = parser.parse_args(args)
  settings = load_settings(options)
  db = open_db(options)
  try:
    print db.status().status
  except IOError:
    print "quickopend not running."

def CMDrawsearch(parser, args):
  """Prints the raw database's results for <query>"""
  parser.add_option('--show-rank', '-r', dest='show_rank', action='store_true', help='Show the ranking of results')
  (options, args) = parser.parse_args(args)

  settings = load_settings(options)
  db = open_db(options)
  if len(args) != 1:
    parser.error('Expected: <query>')
  if not db.has_index:
    print "Database is not fully indexed. Wait a bit or try quickopen status"
    return 255
  res = db.search(args[0])
  if options.show_rank:
    combined = [(res.ranks[i],res.hits[i]) for i in range(len(res.hits))]
    print "\n".join(["%i,%s" % c for c in combined])
  else:
    print "\n".join([x for x in res.hits])

  if len(res.hits) > 0:
    return 0
  return 255

def CMDprelaunch(parser, args):
  """Prestarts a quickopen instance pending network control"""
  parser.add_option("--wait", action="store_true", dest="wait")
  parser.add_option("--control-port", action="store", dest="control_port")
  (options, args) = parser.parse_args(args)
  settings = load_settings(options)
  if options.wait:
    options.control_port = int(options.control_port)
    prelaunch.wait_for_command(options.control_port)
  else:
    prelaunch.run_command_in_existing(options.host, options.port, args)

def load_settings(options):
  settings_file = os.path.expanduser(options.settings)
  settings = src.settings.Settings(settings_file)
  settings.register('host', str, 'localhost')
  settings.register('port', int, -1)
  settings.register('trace', bool, False)

  if settings.port == -1:
    # Open the quickopend settings file to get the default
    # port for the daemon. Then, push that value to the quickopen settings
    daemon_settings_file = os.path.expanduser("~/.quickopend")
    daemon_settings = src.settings.Settings(daemon_settings_file)
    daemon_settings.register('port', int, 10248)
    settings.port = daemon_settings.port

  if not options.host:
    options.host = settings.host
  if not options.port:
    options.port = settings.port
  return settings

def open_db(options):
  return src.db_proxy.DBProxy(options.host, options.port, start_if_needed=True, port_for_autostart=options.port)

# Subcommand addins to optparse, taken from git-cl.py, 
# http://src.chromium.org/svn/trunk/tools/depot_tools/git_cl.py
###########################################################################

def Command(name):
  return getattr(sys.modules[__name__], 'CMD' + name, None)


def CMDhelp(parser, args):
  """print list of commands or help for a specific command"""
  _, args = parser.parse_args(args)
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


def main(argv):
  """Doesn't parse the arguments here, just find the right subcommand to
  execute."""
  # Do it late so all commands are listed.
  CMDhelp.usage_more = ('\n\nCommands are:\n' + '\n'.join([
      '  %-10s %s' % (fn[3:], Command(fn[3:]).__doc__.split('\n')[0].strip())
      for fn in dir(sys.modules[__name__]) if fn.startswith('CMD')]))

  # Create the option parse and add --verbose support.
  parser = optparse.OptionParser()
  parser.add_option(
      '-v', '--verbose', action='count', default=0,
      help='Increase verbosity level (repeat as needed)')
  parser.add_option('--host', dest='host', action='store', help='Hostname of quickopend server')
  parser.add_option('--port', dest='port', action='store', help='Port for quickopend')
  parser.add_option('--settings', dest='settings', action='store', default='~/.quickopen', help='Settings file to use, ~/.quickopen by default')
  parser.add_option('--trace', dest='trace', action='store_true', default=False, help='Records performance tracing information to %s.trace' % sys.argv[0])
  old_parser_args = parser.parse_args
  def Parse(args):
    options, args = old_parser_args(args)
    if options.verbose >= 2:
      logging.basicConfig(level=logging.DEBUG)
    elif options.verbose:
      logging.basicConfig(level=logging.INFO)
    else:
      logging.basicConfig(level=logging.WARNING)
    if options.trace:
      trace_enable("./%s.trace" % sys.argv[0])
    return options, args
  parser.parse_args = Parse

  non_switch_args = [i for i in argv if not i.startswith('-')]
  if non_switch_args:
    command = Command(non_switch_args[0])
    if command:
      # "fix" the usage and the description now that we know the subcommand.
      GenUsage(parser, non_switch_args[0])
      new_args = list(argv)
      new_args.remove(non_switch_args[0])
      return command(parser, new_args)
    # Not a known command. Default to help.
    GenUsage(parser, 'help')
    return CMDhelp(parser, argv)
  else: # default command
    GenUsage(parser, 'search')
    return CMDsearch(parser, argv)
