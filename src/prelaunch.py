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
import socket
import sys
import httplib

def is_prelaunch(args):
  if len(args) >= 2 and args[1] == "prelaunch":
    if len(args) >= 3:
      return args[2] != "--host"
    else:
      return True
  return False

def wait_for_command(control_port):
  s = socket.socket()
  s.bind(("", control_port))
  s.listen(0)
  c, a = s.accept()
  print c, a
  sys.exit(0)

def run_command_in_existing(daemon_host, daemon_port, args):
  # get the pid of a prelaunch process...
  conn = httplib.HTTPConnection(daemon_host, daemon_port, True)
  try:
    conn.request('GET', '/existing_quickopen')
  except socket.error:
    print "quickopend not running." # keep this synchronized with CMDstatus from quickopen.py
    return

  res = conn.getresponse()
  assert res.status == 200
  
  print res.read()
    
