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
import wx
import wx.webkit
import sys
import traceback
import unittest

_hooked = False
_app = None
_current_main_loop_instance = 0
_wx_frame = None # keeps the message loop alive when there aren't any other frames :'(

_pending_tasks_timer = None
_pending_tasks = []
_unittests_running = False
_active_test_result = None
_active_test = None
_quit_handlers = []

def init_main_loop():
  global _hooked
  if not _hooked:
    _hooked = True
    old_hook = sys.excepthook
    def hook(exc, value, tb):
      if is_main_loop_running() and _active_test:
        if isinstance(value,unittest.TestCase.failureException):
          print "hook"
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

  global _app
  if not _app:
    _app = wx.App(False)
    _app.SetAppName("TraceViewer")

    global _wx_frame
    _wx_frame = wx.Frame(None, -1, "KeepMainLoopAlive");

def _run_pending_tasks(e):
  pending = list(_pending_tasks)
  del _pending_tasks[:]
  for cb,args in pending:
    cb(*args)

def post_task(cb, *args):
  init_main_loop()
  global _pending_tasks_timer
  if not _pending_tasks_timer:
    _pending_tasks_timer = wx.Timer(None, -1)
    _pending_tasks_timer.Bind(wx.EVT_TIMER, _run_pending_tasks, _pending_tasks_timer)
  _pending_tasks.append( (cb, args) )

  if not _pending_tasks_timer.IsRunning():
    _pending_tasks_timer.Start(11, True)

def post_delayed_task(cb, delay, *args):
  init_main_loop()
  timer = wx.Timer(None, -1)
  main_loop_instance_at_post = _current_main_loop_instance
  def on_run(e):
    try:
      # timeouts that were enqueued when the mainloop exited should not run
      if _current_main_loop_instance == main_loop_instance_at_post:
        cb(*args)
    finally:
      timer.Destroy()
  timer.Bind(wx.EVT_TIMER, on_run, timer)
  timer.Start(max(1,int(delay * 1000)), True)

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

def is_main_loop_running():
  if not _app:
    return False
  return _app.IsMainLoopRunning()

def run_main_loop():
  global _current_main_loop_instance
  if _unittests_running and not _active_test:
    _current_main_loop_instance += 1 # kill any enqueued tasks
    del _pending_tasks[:]
    del _quit_handlers[:]
    raise Exception("UITestCase must be used for tests that use the message_loop.")

  global _app
  global _pending_tasks_timer
  init_main_loop()

  assert not is_main_loop_running()

  try:
    _app.MainLoop()
  except:
    traceback.print_exc()
  finally:
    _current_main_loop_instance += 1

  del _pending_tasks[:]

  _app.Destroy()
  _app = None

  global _quitting
  _quitting = False

_quitting = False
def quit_main_loop():
  global _current_main_loop_instance
  _current_main_loop_instance += 1
  global _quitting
  if _quitting:
    return
  _quitting = True

  def do_quit():
    global _wx_frame
    if _wx_frame:
      _wx_frame.Destroy()
      _wx_frame = None

    global _pending_tasks_timer
    if _pending_tasks_timer:
      _pending_tasks_timer.Destroy()
      _pending_tasks_timer = None

    for cb in _quit_handlers:
      cb()
    del _quit_handlers[:]

    _app.ExitMainLoop()

  post_task(do_quit)
