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
import pson
import unittest


class PSONTest(unittest.TestCase):
  def setUp(self):
    self._objs = []
    self._strs = []
    self._pretty_strs = []
    def add(o,s,ps=None):
      self._objs.append(o)
      self._strs.append(s)
      if ps:
        if ps[0] == '\n':
          ps = ps[1:]
        self._pretty_strs.append(ps)
      else:
        self._pretty_strs.append(s)
    add(None, "None")
    add(True, "True")
    add(False, "False")
    add("Foo", "\"Foo\"")
    add(u"Foo", u"\"Foo\"")
    add(1, "1")
    add([], "[]")
    add({}, "{}")
    add([1], "[1]")
    add([1,1], "[1,1]", """
[
    1,
    1
]""")
    add([1,2], "[1, 2]","""
[
    1,
    2
]""")
    add({"a":1}, """{"a" : 1}""","""{"a" : 1}""");
    add({"a":1, "b" : 2}, """{"a" : 1, "b" : 2}""","""
{
    "a" : 1,
    "b" : 2
}""")
    add({"a":1, "b" : [1, 2, 3]}, """{"a" : 1, "b" : [1, 2, 3]}""","""
{
    "a" : 1,
    "b" : [
        1,
        2,
        3
    ]
}""")
    add({"a":1, "b" : {"key" : "value"}}, """{"a" : 1, "b" : {"key" : "value"}}""","""
{
    "a" : 1,
    "b" : {"key" : "value"}
}""")
    add({"a":1, "b" : {"key1" : "value1", "key2" : "value2"}}, """{"a" : 1, "b" : {"key1" : "value1", "key2" : "value2"}}""","""
{
    "a" : 1,
    "b" : {
        "key1" : "value1",
        "key2" : "value2"
    }
}""")
    add({"key":[1,2,3]}, """{"key" : [1, 2, 3]}""","""
{
    "key" : [
        1,
        2,
        3
    ]
}""")

  def test_dump(self):
    for i in range(len(self._objs)):
      self.assertEqual(pson.dumps(self._objs[i]),self._strs[i])

  def test_dump(self):
    for i in range(len(self._objs)):
      p = pson.dumps(self._objs[i],pretty=True)
      self.assertEqual(p,self._pretty_strs[i])

  def test_load(self):
    for i in range(len(self._objs)):
      self.assertEqual(pson.loads(self._strs[i]),self._objs[i])
 
