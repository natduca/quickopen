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
import unittest

class TestPrelaunchClient(unittest.TestCase):
  def test_is_prelaunch_client(self):
    self.assertEquals(False, prelaunch_client.is_prelaunch_client([""]))
    self.assertEquals(False, prelaunch_client.is_prelaunch_client(["", "search", "--wait"]))
    self.assertEquals(False, prelaunch_client.is_prelaunch_client(["", "prelaunch", "--wait"]))
    self.assertEquals(True, prelaunch_client.is_prelaunch_client(["", "prelaunch"]))
    self.assertEquals(True, prelaunch_client.is_prelaunch_client(["", "prelaunch", "search"]))

