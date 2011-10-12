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
import objc
import sys
import unittest
from AppKit import *
from Foundation import *
from PyObjCTools import AppHelper

_is_main_loop_running = False
_current_main_loop_instance = 0
_pending_tasks = [] # list of tasks added before the NSApplication runloop began
_quit_handlers = []
_unittests_running = False
_active_test_result = None
_active_test = None
_hooked = False

def _get_cur_app_delegate():
  return NSApplication.sharedApplication().delegate()

class AppDelegate(NSObject):
  def awakeFromNib(self):
    for p in _pending_tasks:
      if p[2] > 0:
        self.performSelectorOnMainThread_withObject_waitUntilDone_(self.runtask, p, False)
      else:
        self.performSelector_withObject_afterDelay_(self.runtask, p, p[2])

  @objc.signature('v@:@')
  def runtask(self, p):
    global _current_main_loop_instance
    # timeouts that were enqueued when the mainloop exited should not run
    if _current_main_loop_instance == p[0]:
      p[1](*p[3])

  @objc.IBAction
  def open_(self, a):
    print "open"

  @objc.IBAction
  def applicationDidFinishLaunching_(self, a):
    pass

  def quit_(self, a):
    print "quit"

  def applicationShouldTerminate_(self, a):
    return True

def _make_call_cb(cb):
  def _call_cb(*inner_args):
    try:
      cb(*inner_args)
    except unittest.TestCase.failureException:
      if _active_test:
        _active_test_result.addFailure(_active_test, sys.exc_info())
        quit_main_loop()
        return
      raise
    except:
      if _active_test:
        _active_test_result.addError(_active_test, sys.exc_info())
        quit_main_loop()
        return
      raise
  return _call_cb

def post_task(cb, *args):
  p = (_current_main_loop_instance, _make_call_cb(cb), 0, args)
  if _is_main_loop_running:
    d = _get_cur_app_delegate()
    d.performSelectorOnMainThread_withObject_waitUntilDone_(d.runtask, p, False)
  else:
    _pending_tasks.append(p)

def post_delayed_task(cb, delay, *args):
  p = (_current_main_loop_instance, _make_call_cb(cb), delay, args)
  if _is_main_loop_running:
    d = _get_cur_app_delegate()
    d.performSelector_withObject_afterDelay_(d.runtask, p, p[2])
  else:
    _pending_tasks.append(p)

def is_main_loop_running():
  return _is_main_loop_running

def init_main_loop():
  global _hooked
  if not _hooked:
    _hooked = True
    old_hook = sys.excepthook
    def hook(exc, value, tb):
      print "hook"
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

  NSApplication.sharedApplication()

def run_main_loop():
  global _current_main_loop_instance
  global _is_main_loop_running
  if _unittests_running and not _active_test:
    _current_main_loop_instance += 1 # kill any enqueued tasks
    raise Exception("UITestCase must be used for tests that use the message_loop.")

  assert not _is_main_loop_running
  _is_main_loop_running = True
  # we will never ever ever return from here. :'(
  AppHelper.runEventLoop(installInterrupt=True,unexpectedErrorAlert=False)


def add_quit_handler(cb):
  _quit_handlers.insert(0, cb)

def set_unittests_running(running):
  global _unittests_running
  _unittests_running = running

def set_active_test(test, result):
  global _active_test
  global _active_test_result
  _active_test = test
  _active_test_result = result

def quit_main_loop():
  global _current_main_loop_instance
  _current_main_loop_instance += 1 # stop any in-flight tasks in case the objc stuff doesn't die promptly
  def do_quit():
    for cb in _quit_handlers:
      cb()
    AppHelper.stopEventLoop() # will actually sys.exit() :'(

  d = _get_cur_app_delegate()
  d.performSelectorOnMainThread_withObject_waitUntilDone_(d.runtask, (_current_main_loop_instance, do_quit, 0, []), False)
