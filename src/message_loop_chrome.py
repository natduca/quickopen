
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
import imp
import os
import sys

def _setupPath():
  path = os.path.join(
    os.path.dirname(__file__),
    "..", "third_party", "py-chrome-app")
  if path not in sys.path:
    sys.path.append(path)
_setupPath()
import chromeapp

_pending_tasks = []
_quit_handlers = []
_is_main_loop_running = False
_unittests_running = False
_active_test = None
_active_test_result = None

def supported():
  # OSX only for now, since GTK is solid elsewhere.
  if sys.platform != 'darwin':
    return False

  if not chromeapp.IsChromeInstalled():
    return False

  try:
    imp.find_module('wx')
    has_wx = True
  except ImportError:
    has_wx = False

  if has_wx:
    return False
  return True

def post_task(cb, *args):
  _pending_tasks.append({
      "cb": cb,
      "args": args})

def post_delayed_task(cb, delay, *args):
  # TODO(nduca): Make this behave properly iff strictly needed it.
  _pending_tasks.append({
      "cb": cb,
      "args": args})

def is_main_loop_running():
  return _is_main_loop_running

def init_main_loop():
  return

def run_main_loop():
  global _pending_tasks
  global _is_main_loop_running
  global _quit_handlers

  if _unittests_running and not _active_test:
    _current_main_loop_instance += 1 # kill any enqueued tasks
    del _quit_handlers[:]
    raise Exception("UITestCase must be used for tests that use the message_loop.")

  _is_main_loop_running = True
  while len(_pending_tasks):
    t = _pending_tasks[0]
    _pending_tasks = _pending_tasks[1:]
    try:
      t["cb"](*t["args"])
    except:
      exc, value, tb = sys.exc_info()
      if _active_test:
        import unittest
        if isinstance(value, unittest.TestCase.failureException):
          _active_test_result.addFailure(_active_test, (exc, value, tb))
        else:
          if not str(value).startswith("_noprint"):
            print "Untrapped exception! Exiting message loop with exception."
          _active_test_result.addError(_active_test, (exc, value, tb))
        quit_main_loop()
        return
      else:
        import traceback
        traceback.print_exc()

  _is_main_loop_running = False

  for cb in _quit_handlers:
    cb()
  del _quit_handlers[:]

def add_quit_handler(cb):
  _quit_handlers.append(cb)

def set_unittests_running(running):
  global _unittests_running
  _unittests_running = running

def set_active_test(test, result):
  global _active_test
  global _active_test_result
  _active_test = test
  _active_test_result = result

def quit_main_loop():
  global _pending_tasks
  _pending_tasks = []

