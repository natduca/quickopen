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
from dyn_object import *
import json

class DynObjectTest(unittest.TestCase):
  def test_base(self):
    o = DynObject()
    o.x = 1
    o.y = 2
    self.assertEqual(1, o.x)
    self.assertEqual(2, o.y)
    d = o.as_dict()

    self.assertEqual(1, d['x'])
    self.assertEqual(2, d['y'])
    o_ = DynObject(o.as_json())
    self.assertEqual(1, o.x)
    self.assertEqual(2, o.y)

    
  def test_cons(self):
    o = DynObject({'x': 1, 'y': 2})
    self.assertEqual(1, o.x)
    self.assertEqual(2, o.y)
    o.x = 2
    self.assertEqual(2, o.x)
    o.z = 3
