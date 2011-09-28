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


# The prelaunchd's job is to keep a quickopen instance warmed up in the
# background, and service "give me a prelauncher" requests from quickopend
# clients.
import os
import subprocess

def _is_port_listening(host, port):
  import socket
  s = socket.socket()
  try:
    s.connect((host, port))
  except socket.error:
    return False
  s.close()
  return True

class PrelaunchDaemon(object):
  def __init__(self, server):
    server.add_json_route('/existing_quickopen', self.get_existing_quickopen, ['GET'])
    self._quickopen = None
    self._cur_control_port = 24712

  def _launch_new_quickopen(self):
    assert not self._quickopen
    quickopen_script = os.path.join(os.path.dirname(__file__), "../quickopen")
    assert os.path.exists(quickopen_script)
    
    assert not _is_port_listening("localhost", self._cur_control_port)

    self._quickopen = subprocess.Popen([quickopen_script,
                                        "--host-prelaunch",
                                        str(self._cur_control_port)])

  def get_existing_quickopen(self, m, verb, data):
    if self.quickopen == None:
      self._launch_new_quickopen()
    try:
      return self._cur_control_port
    finally:
      self._cur_control_port += 1
      self._quickopen = None
      self._launch_new_quickopen()

  def stop(self):
    if self._quickopen:
      self._quickopen.kill()

