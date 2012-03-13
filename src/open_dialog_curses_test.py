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
import unittest
import open_dialog as odc
import open_dialog_curses as odc

class ElideTest(unittest.TestCase):
  def test_elide_nop(self):
    self.assertEquals("x", odc.elide("x", 1))

    self.assertEquals("abc", odc.elide("abcd", 3))
    self.assertEquals("abc", odc.elide("abcdefghijklmn", 3))

    self.assertEquals("a...", odc.elide("abcdefghjiklmn", 4))
    self.assertEquals("a...", odc.elide("abcdefghijklmn", 4))

    self.assertEquals("a...n", odc.elide("abcdefghijklmn", 5))
    self.assertEquals("ab...n", odc.elide("abcdefghijklmn", 6))
