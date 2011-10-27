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
import logging

def _is_port_bindable(host, port):
  import socket
  s = socket.socket()
  try:
    s.bind((host, port))
  except socket.error:
    return False
  s.close()
  return True

class PrelaunchedProcess(object):
  def __init__(self, proc, port):
    if not isinstance(proc, subprocess.Popen):
      raise "Expected subprocess"
    self.proc = proc
    self.port = port

  @property
  def pid(self):
    return self.proc.pid

  def poll(self):
    return self.proc.poll()

  def kill(self):
    self.proc.kill()

class PrelaunchDaemon(object):
  def __init__(self, server):
    server.add_json_route('/existing_quickopen/(.+)', self.get_existing_quickopen, ['GET'])
    server.exit.add_listener(self._on_exit)
    server.lo_idle.add_listener(self._join_in_use_processes)
    self._quickopen = {}
    self._in_use_processes = []
    self._next_control_port = 27412

  def _get_another_control_port(self):
    self._next_control_port += 1
    for i in range(100):
      self._next_control_port += 1
      if not _is_port_bindable("", self._next_control_port):
        continue
      return self._next_control_port
    raise Exception("Could not find open control port")

  def _launch_new_quickopen(self, display):
    assert display not in self._quickopen
    quickopen_script = os.path.join(os.path.dirname(__file__), "../quickopen")
    assert os.path.exists(quickopen_script)

    control_port = self._get_another_control_port()
    proc = subprocess.Popen([quickopen_script,
                             "prelaunch",
                             "--wait",
                             "--control-port",
                             str(control_port)])
    self._quickopen[display] = PrelaunchedProcess(proc, control_port)

  def get_existing_quickopen(self, m, verb, data):
    display = m.group(1)
    if display not in self._quickopen:
      self._launch_new_quickopen(display)
    try:
      proc = self._quickopen[display]
      del self._quickopen[display]

      self._in_use_processes.append(proc)
      return proc.port
    finally:
      # todo, move this to another place... ideally, when the previous prelaunch quits
      self._launch_new_quickopen(display)
      pass

  def _on_exit(self):
    self.stop()

  def _join_in_use_processes(self):
    procs = list(self._in_use_processes)
    del self._in_use_processes[:]
    for p in procs:
      if not p.poll():
        self._in_use_processes.append(p)
      else:
        logging.debug("prelaunched pid=%i is gone" % p.pid)

  def stop(self):
    logging.debug("closing prelaunched quickopen")
    for proc in self._quickopen.values():
      proc.kill()
    self._quickopen = {}

    self._join_in_use_processes()
    for p in self._in_use_processes:
      if not p.poll():
        logging.debug("killing %i" % p.pid)
        try:
          p.kill()
        except:
          pass
