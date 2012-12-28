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
import os
import sys
import socket
import httplib
import time

# Keep imports to a minimum in this file. This is the critial path for a
# "hot" prelaunch, so we want to get a command out to the prelauncher as fast
# as we can manage.

def is_prelaunch_client(args):
  if 'prelaunch' in args[1:]:
    index_of_prelaunch = args.index('prelaunch')
    after_args = args[index_of_prelaunch + 1:]
    return '--wait' not in after_args
  return False

def remove_prelaunch_from_sys_argv():
  index_of_prelaunch = sys.argv.index('prelaunch')
  assert index_of_prelaunch != -1
  del sys.argv[index_of_prelaunch]

def run_command_in_existing(daemon_host, daemon_port, args, auto_start=True):
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

  def existing_quickopen_port():
      conn = httplib.HTTPConnection(daemon_host, daemon_port, True)
      conn.request('GET', '/existing_quickopen/%s' % display)
      res = conn.getresponse()
      assert res.status == 200
      port = int(res.read())
      return port

  # Get the pid of an existing quickopen process via
  # quickopend. This routes through prelaunchd.py
  try:
    port = existing_quickopen_port()
  except socket.error:
    if not auto_start:
      from db_status import DBStatus
      return "%s.\n" % DBStatus.not_running_string()

    # quickopend not started; attempt once to start it automatically
    import StringIO
    try:
      # Squelch any output from starting the db
      orig_stdout = sys.stdout
      orig_stderr = sys.stderr
      sys.stdout = StringIO.StringIO()
      sys.stderr = sys.stdout

      sys.path.append(os.path.join(os.path.dirname(__file__), "../third_party/py_trace_event/"))
      import db_proxy
      db_proxy.DBProxy.try_to_start_quickopend(daemon_port)
      try:
        port = existing_quickopen_port()
      except socket.error:
        from db_status import DBStatus
        return "%s.\n" % DBStatus.not_running_string()
    finally:
      sys.stdout = orig_stdout
      sys.stderr = orig_stderr

  # Get a connection to the prelaunched process.
  # We may have to try a few times --- it may be coming up still.
  connected = False
  s = None
  for i in range(20): # 5 seconds
    try:
      s = socket.socket()
      s.connect((daemon_host, port))
      break
    except:
      time.sleep(0.25)
  if not s:
    raise Exception("Could not connect to the provided process.")
  try:
    f = s.makefile()

    # Send our commandline to the existing quickopend. Pass with it our
    # daemon_host and daemon_port so that it tries talking to the same quickopend
    # instance as us.
    full_args = list(args)
    full_args.extend(["--host=%s" % daemon_host])
    full_args.extend(["--port=%s" % str(daemon_port)])
    f.write(repr(full_args))
    f.write("\n")
    f.flush()

    # Wait for the result of the quickopening. It comes over as a repr'd string
    # so eval it to get the real multi-line string.
    l = eval(f.readline(), {}, {})
    return l
  finally:
    s.close()

def main(in_args):
  # poor mans host and port processing to avoid importing OptParse
  port = default_port.get()
  host = 'localhost'
  auto_start = True
  before_args = [] # remaining after poor-mans parse but befor 'prelaunch' command
  after_args = None
  i = 1
  while i < len(in_args):
    if in_args[i].startswith('--host='):
      host = in_args[i][7:]
      i += 1
      continue

    if in_args[i].startswith('--port='):
      port = in_args[i][7:]
      i += 1
      continue

    if in_args[i] == '--no_auto_start':
      auto_start = False
      i += 1
      continue

    if in_args[i] == 'prelaunch':
      after_args = in_args[i+1:]
      break

    before_args.append(in_args[i])
    i += 1

  if after_args == None:
    raise Exception("Expected: prelaunch")
  assert len(before_args) == 0
  if len(after_args) == 0:
    after_args.append("search")

  try:
    sys.stdout.write(run_command_in_existing(host, port, after_args, auto_start))
    return 0
  except Exception as e:
    sys.stdout.write(str(e) + "\n")
    return -1
