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
import temporary_daemon
import unittest
from quickopen_test_base import QuickopenTestBase

class PrelaunchTest(unittest.TestCase, QuickopenTestBase):
  def setUp(self):
    unittest.TestCase.setUp(self)
    QuickopenTestBase.setUp(self)
    self.daemon = temporary_daemon.TemporaryDaemon()

  def qo(self, cmd, *args):
    full_args = [cmd]
    full_args.extend(args)
    return prelaunch_client.run_command_in_existing(self.daemon.host, self.daemon.port, full_args)

  def turn_off_daemon(self):
    self.daemon.close()

  def tearDown(self):
    unittest.TestCase.tearDown(self)
    QuickopenTestBase.tearDown(self)
    self.daemon.close()
