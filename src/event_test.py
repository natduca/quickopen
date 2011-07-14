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
from event import *
import unittest

class EventTest(unittest.TestCase):
  def test_event(self):
    e = Event()
    fired = []
    def l(*args):
      self.assertEqual(3, args[0])
      fired.append(True)
    e.add_listener(l)
    e.fire(3)
    self.assertEqual(1, len(fired))

    e.remove_listener(l)
    del fired[:]
    e.fire(3)
    self.assertEqual(0, len(fired))

  def test_event_that_raises_doesnt_reraise(self):
    e = Event()
    def l():
      raise Exception()
    e.add_listener(l)
    e.fire_silent()

  def test_last_return(self):
    e = Event()
    def l1():
      return 1
    def l2():
      return 2
    e.add_listener(l1)
    e.add_listener(l2)
    self.assertEqual(2, e.fire())
