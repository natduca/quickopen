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
import message_loop
import unittest

from ui_test_case import *

"""
The tests below follow the basic pattern:
 - subclass UITestCase with a method called "test" that will
   be the actual test code
 - run the test case --- if things are working, this should relaunch the test
   in a subprocess and run it.
 - verify that either the uitest was successful or failed,
   depending on the test

"""

class _TestThatSucceedsInsideMessageLoop(UITestCase):
  def test(self):
    def go():
      self.assertEquals(True, True)
      message_loop.quit_main_loop()
    message_loop.post_task(go)

class _TestThatFailsInsideMessageLoop(UITestCase):
  def test(self):
    def go():
      self.assertEquals(False, True)
    message_loop.post_task(go)

class _TestThatRaisesInsideMessageLoop(UITestCase):
  def test(self):
    def go():
      raise Exception("_noprint Generic error")
    message_loop.post_task(go)

class UITestCaseTest(unittest.TestCase):
  def test_test_that_succeeds_inside_message_loop(self):
    test = _TestThatSucceedsInsideMessageLoop("test")
    result = unittest.TestResult()
    test.run(result)
    if not result.wasSuccessful():
      for t, e in result.errors:
        print e
      for t, e in result.failures:
        print e
    self.assertTrue(result.wasSuccessful())

  def test_test_that_fails_inside_message_loop(self):
    test = _TestThatFailsInsideMessageLoop("test")
    result = unittest.TestResult()
    test.run(result)
    self.assertFalse(result.wasSuccessful())
    self.assertEquals(1, len(result.failures))
    self.assertEquals(0, len(result.errors))

  def test_test_that_raises_inside_message_loop(self):
    test = _TestThatRaisesInsideMessageLoop("test")
    result = unittest.TestResult()
    test.run(result)
    self.assertFalse(result.wasSuccessful())
    self.assertEquals(0, len(result.failures))
    self.assertEquals(1, len(result.errors))
