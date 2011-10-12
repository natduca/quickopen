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
import glib
import gtk
import sys
import unittest

_hooked = False
_is_main_loop_running = False
_current_main_loop_instance = 0
_unittests_running = False
_active_test_result = None
_active_test = None
_quitting = False
_quit_handlers = []

def init_main_loop():
  global _hooked
  if not _hooked:
    _hooked = True
    old_hook = sys.excepthook
    def hook(exc, value, tb):
      if is_main_loop_running() and _active_test:
        if isinstance(value,unittest.TestCase.failureException):
          _active_test_result.addFailure(_active_test, (exc, value, tb))
        else:
          if not str(value).startswith("_noprint"):
            print "Untrapped exception! Exiting message loop with exception."
          _active_test_result.addError(_active_test, (exc, value, tb))
        quit_main_loop()
        return
      else:
        old_hook(exc, value, tb)
        return
    sys.excepthook = hook

def post_task(cb, *args):
  init_main_loop()
  main_loop_instance_at_post = _current_main_loop_instance
  def on_run():
    # timeouts that were enqueued when the mainloop exited should not run
    if _current_main_loop_instance == main_loop_instance_at_post:
      cb(*args)
  glib.timeout_add(0, on_run)

def post_delayed_task(cb, delay, *args):
  init_main_loop()
  main_loop_instance_at_post = _current_main_loop_instance
  def on_run():
    # timeouts that were enqueued when the mainloop exited should not run
    if _current_main_loop_instance == main_loop_instance_at_post:
      cb(*args)
  timeout_ms = int(delay * 1000)
  glib.timeout_add(timeout_ms, on_run)

def set_unittests_running(running):
  global _unittests_running
  _unittests_running = running

def set_active_test(test, result):
  global _active_test
  global _active_test_result
  _active_test = test
  _active_test_result = result

def is_main_loop_running():
  return _is_main_loop_running

def add_quit_handler(cb):
  _quit_handlers.insert(0, cb)

def run_main_loop():
  global _current_main_loop_instance
  global _is_main_loop_running
  if _unittests_running and not _active_test:
    _current_main_loop_instance += 1 # kill any enqueued tasks
    del _quit_handlers[:]
    raise Exception("UITestCase must be used for tests that use the message_loop.")

  init_main_loop()

  assert not _is_main_loop_running

  try:
    _is_main_loop_running = True
    gtk.main()
  finally:
    _is_main_loop_running = False
    _current_main_loop_instance += 1

  global _quitting
  _quitting = False


def quit_main_loop():
  assert is_main_loop_running()

  global _quitting
  if _quitting:
    return
  _quitting = True

  def do_quit():
    global _current_main_loop_instance
    _current_main_loop_instance += 1

    for cb in _quit_handlers:
      cb()
    del _quit_handlers[:]

    gtk.main_quit()
  post_task(do_quit)
