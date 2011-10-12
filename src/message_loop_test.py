#!/usr/bin/env python
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
import os
import unittest
import message_loop
from ui_test_case import *

class MessageLoopTest(UITestCase):
  def test_post_task(self):
    def step2():
      self.assertTrue(message_loop.is_main_loop_running())
      message_loop.quit_main_loop()
    message_loop.post_task(step2)

  def test_post_two_tasks(self):
    def step2():
      self.assertTrue(message_loop.is_main_loop_running())
      message_loop.post_task(step3)
    def step3():
      self.assertTrue(message_loop.is_main_loop_running())
      message_loop.quit_main_loop()
    message_loop.post_task(step2)

  def test_is_main_loop_running(self):
    def step2():
      self.assertTrue(message_loop.is_main_loop_running())
      message_loop.quit_main_loop()
    message_loop.post_task(step2)

  def test_post_delayed_task(self):
    def step2():
      message_loop.quit_main_loop()
    message_loop.post_delayed_task(step2, 0.1)

  # UITestCaseTest tests that assertions failing will stop the test

class MessageLoopTest2(unittest.TestCase):
  def test_message_loop_wont_run_in_regular_testcase(self):
    def shouldnt_run():
      raise Exception("Shouldn't ever get here")
    message_loop.post_task(shouldnt_run)
    self.assertRaises(Exception, lambda: message_loop.run_main_loop())
