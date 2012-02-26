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

# The prelauncher's job is to delegate the quickopen commandline interface
# to an already "warmed-up" instance of quiclpen launched by the quickopend.
#
# Importing python GUI libraries is actually quite slow. We want to give
# users of quickopen a nice snappy experience. So, the prelaunchd counterpart
# of this code keeps around a "warmed up" quickopen instance in the background.
#
# When a new quickopen comes around with a --use-prelaunch, it consults
# the daemon for prelaunched instance handle and then delegates its actual
# commandline to that instance (via magic).
import os
import socket
import sys
import httplib
import time
import StringIO

from trace_event import *

_is_prelaunched_process = False

def is_prelaunched_process():
  return _is_prelaunched_process

def wait_for_command(control_port):
  global _is_prelaunched_process
  _is_prelaunched_process = True

  s = socket.socket()
  try:
    trace_begin("bind_to_control_port")
    bound = False
    for i in range(10):
      try:
        s.bind(("", control_port))
        bound = True
        break
      except socket.error:
        time.sleep(0.1)
    if not bound:
      raise Exception("could not bind!")
    trace_end("bind_to_control_port")

    s.listen(1)
    trace_begin("socket.accept")
    c, a = s.accept()
    trace_end("socket.accept")
    f = c.makefile()

    # The commandline comes in as a repr'd array
    # Yes this is not very secure. Donations welcome.
    trace_begin("read_command")
    args = eval(f.readline(), {}, {})
    trace_end("read_command")

    # We want to send the commandline args to quickopen's regular
    # main now, and redirect the stdout output over to the prelauncher.
    # We do this by overriding stdout to a StringIO. It works, though
    # we could technically do better.
    import quickopen
    import optparse
    old_stdout = sys.stdout
    new_stdout = StringIO.StringIO()
    sys.stdout = new_stdout
    old_argv = sys.argv
    try:
      sys.argv = [sys.argv[0]]
      sys.argv.extend(args)
      parser = optparse.OptionParser(usage=quickopen.main_usage())
      quickopen.main(parser)
    except:
      sys.stdout = old_stdout
      import traceback
      traceback.print_exc()
    finally:
      sys.argv = old_argv
      sys.stdout = old_stdout

    trace_end("exec_command")

    # Finally, give the results back to the prelauncher so that
    # it can do its work. Pass the string via repr so we can use
    # a single readline command to do the heavy lifting for us. :)
    v = new_stdout.getvalue()
    f.write(repr(v))
    f.write("\n")
    f.close()
  finally:
    s.close()
    sys.exit(0)

@traced
def run_command_in_existing(daemon_host, daemon_port, args):
  # Prelaunched processes are DISPLAY-specific
  if sys.platform == 'darwin':
    if os.getenv('DISPLAY'):
      display = os.getenv('DISPLAY')
    else:
      display = 'cocoa'
  else:
    if os.getenv('DISPLAY'):
      display = os.getenv('DISPLAY')
    else:
      display = 'terminal';

  # Get the pid of an existing quickopen process via
  # quickopend. This routes through prelaunchd.py
  trace_begin("get_existing_quickopen")
  conn = httplib.HTTPConnection(daemon_host, daemon_port, True)
  try:
    conn.request('GET', '/existing_quickopen/%s' % display)
  except socket.error:
    raise Exception("quickopend not running.")

  res = conn.getresponse()
  assert res.status == 200
  port = int(res.read())
  trace_end("get_existing_quickopen")

  # Get a connection to the prelaunched process.
  # We may have to try a few times --- it may be coming up still.
  trace_begin("connect_to_prelaunched_qo")
  connected = False
  s = None
  for i in range(20): # 5 seconds
    try:
      s = socket.socket()
      s.connect(("localhost", port))
      break
    except:
      time.sleep(0.25)
  trace_end("connect_to_prelaunched_qo")
  if not s:
    raise Exception("Could not connect to the provided process.")
  try:
    f = s.makefile()

    # Send our commandline to the existing quickopend. Pass with it our
    # daemon_host and daemon_port so that it tries talking to the same quickopend
    # instance as us.
    full_args = list(args)
    full_args.extend(["--host", daemon_host])
    full_args.extend(["--port", str(daemon_port)])
    f.write(repr(full_args))
    f.write("\n")
    f.flush()

    # Wait for the result of the quickopening. It comes over as a repr'd string
    # so eval it to get the real multi-line string.
    trace_begin("read_result")
    l = eval(f.readline(), {}, {})
    trace_end("read_result")
    return l
  finally:
    s.close()
