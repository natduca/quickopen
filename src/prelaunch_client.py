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
  if len(args) >= 2 and args[1] == "prelaunch":
    if len(args) >= 3:
      return args[2] != "--wait"
    else:
      return True
  return False

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
  conn = httplib.HTTPConnection(daemon_host, daemon_port, True)
  try:
    conn.request('GET', '/existing_quickopen/%s' % display)
  except socket.error:
    from db_status import DBStatus
    return "%s.\n" % DBStatus.not_running_string()

  res = conn.getresponse()
  assert res.status == 200
  port = int(res.read())

  # Get a connection to the prelaunched process.
  # We may have to try a few times --- it may be coming up still.
  connected = False
  s = None
  for i in range(20): # 5 seconds
    try:
      s = socket.socket()
      s.connect(("localhost", port))
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
    full_args.extend(["--host", daemon_host])
    full_args.extend(["--port", str(daemon_port)])
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
  before_args = [] # remaining after poor-mans parse but befor 'prelaunch' command
  after_args = None
  i = 1
  while i < len(in_args):
    if in_args[i] == '--host':
      host = in_args[i+1]
      i += 1
      continue

    if in_args[i] == '--port':
      port = in_args[i+1]
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
    sys.stdout.write(run_command_in_existing(host, port, after_args))
    return 0
  except Exception as e:
    sys.stdout.write(str(e) + "\n")
    return -1
