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
import prelaunch_client
import os
import sys

def run(prelaunch=False):
  """Called by bootstrapper when the environment is ready to run."""
  if sys.argv[1] != '--main-name':
    raise Exception("launched wrong: expected --main-name <mainname> as first argument")
  main_name = sys.argv[2]
  del sys.argv[1:3] # remove the --main-name argument

  thirdpartydir = os.path.join(os.path.dirname(__file__), "../third_party")
  tracedir = os.path.join(thirdpartydir, "py_trace_event")

  # A recent change to py_trace_event leaves an old trace_event dir with .pyc files
  # hanging around. This prevents importing the new trace_event. Clobber it if it is found.
  tracedir_old_style_traceevent = os.path.join(tracedir, "trace_event")
  if os.path.exists(tracedir) and os.path.exists(tracedir_old_style_traceevent) and os.path.isdir(tracedir_old_style_traceevent):
    for root, dirs, files in os.walk(tracedir_old_style_traceevent, False, None, False):
      for f in files:
        os.unlink(os.path.join(root, f))
      for d in dirs:
        os.rmdir(os.path.join(root, d))
    os.rmdir(tracedir_old_style_traceevent)

  # Import trace event.
  sys.path.append(tracedir)
  try:
    __import__("trace_event")
  except:
    print "Could not find py_trace_event. Did you forget 'git submodule update --init'?"
    sys.exit(255)

  # Import python-daemon.
  sys.path.append(os.path.join(thirdpartydir, "python-daemon/daemon"))
  try:
    __import__("daemon")
  except:
    print "Could not find python-daemon. Did you forget 'git submodule update --init'?"
    sys.exit(255)

  # Import PyGithub.
  sys.path.append(os.path.join(thirdpartydir, "PyGithub/github"))
  try:
    __import__("Github")
  except:
    print "Could not find PyGithub. Did you forget 'git submodule update --init'?"
    sys.exit(255)

  mod = __import__(main_name, {}, {}, True)
  import optparse
  parser = optparse.OptionParser(usage=mod.main_usage())
  parser.add_option('--chrome', action="store_true", dest="chrome", help="Use chrome app UI")
  parser.add_option('--curses', action="store_true", dest="curses", help="Use curses UI")
  parser.add_option(
      '-v', '--verbose', action='count', default=0,
      help='Increase verbosity level (repeat as needed)')
  original_parse_args = parser.parse_args
  def parse_args_shim():
    options, args = original_parse_args()
    handle_options(options, args)
    return options, args
  parser.parse_args = parse_args_shim

  return mod.main(parser)

def handle_options(options, args):
  """Called by bootstrapper to process global commandline options."""
  import logging
  if options.verbose >= 2:
    logging.basicConfig(level=logging.DEBUG)
  elif options.verbose:
    logging.basicConfig(level=logging.INFO)
  else:
    logging.basicConfig(level=logging.WARNING)

def main(main_name):
  """The main entry point to the bootstrapper. Call this with the module name to
  use as your main app."""
  # prelaunch should bypass full bootstrap
  if prelaunch_client.is_prelaunch_client(sys.argv):
    # This is a lightweight import due to lazy initialization of the message loop.
    import message_loop
    if message_loop.supports_prelaunch():
      return sys.exit(prelaunch_client.main(sys.argv))

    # Remove the prelaunch command from the argv and proceed as normal.
    prelaunch_client.remove_prelaunch_from_sys_argv()

  if sys.platform == 'darwin':
    if ('--chrome' in sys.argv):
      sys.argv.insert(1, '--main-name')
      sys.argv.insert(2, main_name)
      sys.exit(run())

    if ('--curses' in sys.argv):
      sys.argv.insert(1, '--main-name')
      sys.argv.insert(2, main_name)
      sys.exit(run())

    # Try using chrome.
    import message_loop_chrome
    if message_loop_chrome.supported():
      sys.argv.insert(1, '--main-name')
      sys.argv.insert(2, main_name)
      sys.exit(run())

    # To use wx-widgets on darwin, we need to be in 32 bit mode. Import of wx
    # will fail if you run python in 64 bit mode, which is default in 10.6+. :'(
    # It is depressingly hard to force python into 32 bit mode reliably across
    # computers, for some reason. So, we try two approaches known to work... one
    # after the other.
    wx_found_but_failed = False
    try:
      import wx
    except ImportError:
      if str(sys.exc_value).find("no appropriate 64-bit") != -1:
        wx_found_but_failed = True

    if wx_found_but_failed:
      # Switch the executable to /usr/bin/python2.6 if we are implicitly running
      # 2.6 via /usr/bin/python. For some reason, neither the arch trick nor the
      # env trick work if you use /usr/bin/python
      if sys.version.startswith("2.6") and sys.executable == '/usr/bin/python':
        if os.path.exists('/usr/bin/python2.6'):
          executable = '/usr/bin/python2.6'
        else:
          executable = sys.executable
      else:
        executable = sys.executable

      # try using the versioner trick
      if '--triedenv' not in sys.argv:
        os.putenv('VERSIONER_PYTHON_PREFER_32_BIT', 'yes')
        args = [executable, sys.argv[0], '--triedenv']
        args.extend(sys.argv[1:])
        os.execve(args[0], args, os.environ)

      # last chance...
      if '--triedarch' not in sys.argv:
        args = ["/usr/bin/arch", "-i386", executable, sys.argv[0], '--triedarch']
        args.extend(sys.argv[1:])
        os.execv(args[0], args)

      # did we already try one of the tricks below? Bail out to prevent recursion...
      print "Your system's python is 64 bit, and all the tricks we know to get it into 32b mode failed."
      sys.exit(255)

    else:
      try:
        sys.argv.remove('--triedenv')
      except:
        pass
      try:
        sys.argv.remove('--triedarch')
      except:
        pass
      sys.argv.insert(1, '--main-name')
      sys.argv.insert(2, main_name)
      sys.exit(run())

  else:
    sys.argv.insert(1, '--main-name')
    sys.argv.insert(2, main_name)
    sys.exit(run())
