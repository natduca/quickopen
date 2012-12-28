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
import subprocess
import temporary_daemon
import unittest
import message_loop
from quickopen_test_base import QuickopenTestBase

class PrelaunchTest(unittest.TestCase, QuickopenTestBase):
  def setUp(self):
    unittest.TestCase.setUp(self)
    QuickopenTestBase.setUp(self)
    self.daemon = temporary_daemon.TemporaryDaemon()

  def qo(self, cmd, *args):
    quickopen_script = os.path.join(os.path.dirname(__file__), "../quickopen")
    assert os.path.exists(quickopen_script)

    full_args = [quickopen_script,
                 "--host=%s" % self.daemon.host,
                 "--port=%s" % str(self.daemon.port),
                 "--no_auto_start",
                 'prelaunch',
                 cmd]
    full_args.extend(args)
    proc = subprocess.Popen(full_args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    if len(stderr):
      print "Error during %s:\n%s\n\n" % (args, stderr)
    return stdout

  def turn_off_daemon(self):
    self.daemon.close()

  def tearDown(self):
    unittest.TestCase.tearDown(self)
    QuickopenTestBase.tearDown(self)
    self.daemon.close()
