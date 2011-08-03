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
from fixed_size_dict import *
import unittest

class FixedSizeDictTest(unittest.TestCase):
  def test_1(self):
    d = FixedSizeDict(2)
    d[1] = "a"
    self.assertEquals(d[1], "a")
    d[2] = "b"
    self.assertEquals(d[2], "b")
    assert 1 in d
    assert 2 in d
    d[2] = "c"
    self.assertEquals(d[2], "c")
    assert 1 in d
    assert 2 in d

  def test_2(self):
    d = FixedSizeDict(2)
    d[1] = "a"
    d[2] = "b"
    self.assertEquals(d[2], "b")
    assert 1 in d
    assert 2 in d
    d[3] = "c"
    self.assertEquals(d[3], "c")
    assert 1 not in d
    assert 2 in d
    assert 3 in d

  def test_3(self):
    d = FixedSizeDict(2)
    d[1] = "a"
    self.assertEquals(d[1], "a")
    d[2] = "b"
    self.assertEquals(d[2], "b")
    d[1] = "a_"
    self.assertEquals(d[1], "a_")
    assert 1 in d
    assert 2 in d
    d[3] = "c"
    self.assertEquals(d[3], "c")
    assert 1 in d
    assert 2 not in d
    assert 3 in d

  def test_4(self):
    d = FixedSizeDict(2)
    d[1] = "a"
    d[2] = "b"
    self.assertEquals(d[2], "b")
    self.assertEquals(d[1], "a")
    assert 1 in d
    assert 2 in d
    d[3] = "c"
    self.assertEquals(d[3], "c")
    assert 1 in d
    assert 2 not in d
    assert 3 in d

