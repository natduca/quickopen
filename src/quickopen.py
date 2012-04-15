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
import default_port
import logging
import message_loop
import optparse
import os
import platform
import prelaunch
import re
import sys

from db_exception import DBException
from db_status import DBStatus
from query import Query

sys.path.append(os.path.join(os.path.dirname(__file__), "../third_party/py_trace_event/"))
try:
  from trace_event import *
except:
  print "Could not find py_trace_event. Did you forget 'git submodule update --init'"
  sys.exit(255)

import src.db_proxy

###########################################################################

def CMDadd(parser):
  """Adds a directory to the index"""
  (options, args) = parser.parse_args()
  db = open_db(options)
  if len(args) == 0:
    parser.error('Expected at least one directory')
  ok = True
  for d in args:
    try:
      db.add_dir(d)
    except DBException, ex:
      ok = False
      print ex.args[0]
  if not ok:
    return 255
  return 0

def CMDdirs(parser):
  """Lists currently-indexed directories"""
  (options, args) = parser.parse_args()
  db = open_db(options)
  if len(args):
    parser.error('Unrecognized args: %s' % ' '.join(args))
  print "\n".join([x.path for x in db.dirs])
  return 0

def CMDrmdir(parser):
  """Removes a currently-indexed directory"""
  (options, args) = parser.parse_args()
  db = open_db(options)
  dmap = {}
  for d in db.dirs:
    dmap[d.path] = d
  ok = True
  for d in args:
    found = False
    for k in dmap.keys():
      try:
        same = os.path.samefile(d, k)
      except:
        same = False
      if same:
        db.delete_dir(dmap[k])
        print "%s removed" % dmap[k].path
        found = True
        break
    if not found:
      print "%s is not indexed." % d
      ok = False
  if ok:
    return 0
  return 255

def CMDignore(parser):
  """Ignores files matching the given regexp"""
  (options, args) = parser.parse_args()
  db = open_db(options)
  if len(args) == 0:
    parser.error('Expected at least one directory')
  for i in args:
    db.ignore(i)
  return 0

def CMDignores(parser):
  """Lists currently-ignored files"""
  (options, args) = parser.parse_args()
  db = open_db(options)
  if len(args):
    parser.error('Unrecognized args: %s' % ' '.join(args))
  print "\n".join(db.ignores)
  return 0

def CMDunignore(parser):
  """Stops ignoring a given regexp"""
  (options, args) = parser.parse_args()
  db = open_db(options)
  ignores = db.ignores
  ok = True
  for i in args:
    if i not in ignores:
      ok = False
      print "%s not found" % i
    else:
      db.unignore(i)
      print "%s removed" % i
  if ok:
    return 0
  return 255

def split_open_filenames(open_filenames):
  # TODO(nduca): deal correctly with \: not being a delimiter
  return open_filenames.split(":")

@traced
def CMDsearch(parser):
  """Search for a file"""
  if prelaunch.is_prelaunched_process() and message_loop.is_curses:
    print "Prelaunching not available for curses UI."
    return 255

  parser.add_option('--ok', dest='ok', action='store_true', default=False, help='Output "OK" before results')
  parser.add_option('--lisp-results', dest='lisp_results', action='store_true', default=False, help='Output results as a lisp-formatted list')
  parser.add_option('--results-file', dest='results_file', action='store', help='Output results to the provided file instead of stdout')
  parser.add_option('--skip-ui-if-exact-match', dest='skip_if_exact', action='store_true', default=False, help="Don't show UI if there's an exact match")
  parser.add_option('--only-if-exact-match', dest='only_if_exact', action='store_true', default=False, help="Print only if there is an exact match, nothing otherwise")
  parser.add_option('--current-filename', dest='current_filename', action='store', default=None, help="Hints quickopen about the current buffer to improve search relevance.")
  parser.add_option('--open-filenames', dest='open_filenames', action='store', default=[], help="Hints quickopen about the filenames currently open to improve search relevance.")
  (options, args) = parser.parse_args()
  message_loop.ensure_has_message_loop()
  if not trace_is_enabled() and options.trace:
    trace_enable("%s.trace" % sys.argv[0])
  db = open_db(options)

  def print_results(res, canceled):
    if options.ok and not canceled:
      print "OK"

    if options.results_file:
      ofile = open(options.results_file, 'w')
    else:
      ofile = sys.stdout

    if options.lisp_results:
      ofile.write("(%s)\n" % (" ".join(['"%s"' % x for x in res])))
    else:
      ofile.write("\n".join(res))
    ofile.write("\n")

    if options.results_file:
      ofile.close()

  search_args = {}
  if options.current_filename:
    search_args["current_filename"] = options.current_filename
  if options.open_filenames:
    # Switch the options to the parsed form so the open dialog can use it directly.
    options.open_filenames = split_open_filenames(options.open_filenames)
    search_args["open_filenames"] = options.open_filenames
  # FIXME: Modify emacs to not use this option anymore and then remove it.
  if options.skip_if_exact:
    res = db.search(args[0], exact_match=True, **search_args)
    if len(res.filenames) == 1:
      print_results(res.filenames, False)
      return 0
  if options.only_if_exact:
    res = db.search(args[0], exact_match=True, **search_args)
    if len(res.filenames) == 1:
      print_results(res.filenames, False)
    return 0

  if len(args):
    initial_filter = " ".join(args)
  else:
    initial_filter = None

  import src.open_dialog as open_dialog
  open_dialog.run(options, db, initial_filter, print_results) # will not return on osx.

def CMDstatus(parser):
  """Checks the status of the quick open database"""
  (options, args) = parser.parse_args()
  db = open_db(options)
  print "%s." % db.status().status

def CMDreindex(parser):
  """Begins to reindex the quickopen database"""
  (options, args) = parser.parse_args()
  db = open_db(options)
  try:
    db.begin_reindex()
    print "Reindexing has begun."
  except IOError:
    print "%s." % DBStatus.not_running_string()

def CMDrawsearch(parser):
  """Prints the raw database's results for <query>"""
  parser.add_option('--show-rank', '-r', dest='show_rank', action='store_true', help='Show the ranking of results')
  parser.add_option('--current-filename', dest='current_filename', action='store', default=None, help="Hints quickopen about the current buffer to improve search relevance.")
  parser.add_option('--open-filenames', dest='open_filenames', action='store', default=[], help="Hints quickopen about the filenames currently open to improve search relevance.")
  parser.add_option('--debug', dest='debug', action='store_true', default=False, help='Debug the query instead of executing it')
  (options, args) = parser.parse_args()

  db = open_db(options)
  if len(args) != 1:
    parser.error('Expected: <query>')
  if not db.has_index:
    print "Database is not fully indexed. Wait a bit or try quickopen status"
    return 255

  search_args = {}
  if options.current_filename:
    search_args["current_filename"] = options.current_filename
  if options.open_filenames:
    search_args["open_filenames"] = split_open_filenames(options.open_filenames)

  q = Query(args[0],**search_args)
  if options.debug:
    q.debug = True
  res = db.search(q)
  if options.debug:
    import pprint
    print pprint.pprint(res.as_dict())
  elif options.show_rank:
    combined = res.hits()
    print "\n".join(["%i,%s" % (c[1],c[0]) for c in combined])
  else:
    print "\n".join([x for x in res.filenames])

  if len(res.filenames) > 0:
    return 0
  return 255

def CMDprelaunch(parser):
  """Performs a quickopen command in a prelaunched instance. Reduces delay in seeing the initial search dialog."""
  args = sys.argv[1:]
  if not "--wait" in args:
    print "Error: prelaunch command must have a --wait in it if it got this far. There must be a bug in the bootstrap."

  parser.add_option("--wait", action="store_true", dest="wait")
  parser.add_option("--control-port", action="store", dest="control_port")
  (options, args) = parser.parse_args()
  assert options.wait
  options.control_port = int(options.control_port)
  prelaunch.wait_for_command(options.control_port)

@traced
def open_db(options):
  return src.db_proxy.DBProxy(options.host, options.port, start_if_needed=False, port_for_autostart=options.port)

# Subcommand addins to optparse, taken from git-cl.py, 
# http://src.chromium.org/svn/trunk/tools/depot_tools/git_cl.py
###########################################################################

def Command(name):
  return getattr(sys.modules[__name__], 'CMD' + name, None)


def CMDhelp(parser):
  """print list of commands or help for a specific command"""
  _, args = parser.parse_args()
  if len(args) == 1:
    sys.argv = [args[0], '--help']
    GenUsage(parser, 'help')
    return CMDhelp(parser)
  # Do it late so all commands are listed.
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
  return "Usage: quickopen [global options] <command> [command arguments]"

def main(parser):
  """Doesn't parse the arguments here, just find the right subcommand to
  execute."""
  # Create the option parse and add --verbose support.
  parser.add_option('--host', dest='host', action='store', help='Hostname of quickopend server. Default is %i' % default_port.get())
  parser.add_option('--port', dest='port', action='store', help='Port for quickopend')
  parser.add_option('--trace', dest='trace', action='store_true', default=False, help='Records performance tracing information to quickopen.trace')
  old_parser_args = parser.parse_args
  def parse():
    options, args = old_parser_args()
    if options.trace:
      trace_enable("./%s.trace" % "quickopen")
    if not options.host:
      options.host = 'localhost'
    if not options.port:
      options.port = default_port.get()
    else:
      options.port = int(options.port)
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
    CMDsearch.usage_more = ('\n\nCommands are:\n' + '\n'.join([
          '  %-10s %s' % (fn[3:], getdoc(Command(fn[3:])).split('\n')[0].strip())
          for fn in dir(sys.modules[__name__]) if fn.startswith('CMD')]))
    GenUsage(parser, 'search')
    return CMDsearch(parser)
