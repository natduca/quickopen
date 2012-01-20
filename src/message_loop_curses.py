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
import curses
import event
import select
import sys
import time
import traceback
import unittest
import cStringIO

# Set the following to True in order to redirect stdout to
#   /tmp/quickopen.stdout
DEBUG = False

_main_loop_running = False

_delayed_task_next_seq = 0
class DelayedTask(object):

  def __init__(self, cb, delay):
    # get a sequence number for this task to break ties
    global _delayed_task_next_seq
    self.seq = _delayed_task_next_seq

    self.cb = cb
    self.run_at_or_after = time.time() + delay
    _delayed_task_next_seq += 1

  def __cmp__(self, that):
    x = cmp(self.run_at_or_after, that.run_at_or_after)
    if x == 0:
      return cmp(self.seq, that.seq)
    else:
      return x

_pending_delayed_tasks = []
_unittests_running = False
_active_test_result = None
_active_test = None
_quit_handlers = []
_quitting = False

_stdscr = None

# exported
on_terminal_readable = event.Event()

# exported
def get_stdscr():
  return _stdscr

def _on_exception():
  import traceback
  traceback.print_exc()
  print "exception"
  return
  #exc, value, tb = sys.exc_info()
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

def _run_pending_tasks():
  now = time.time()
  old_pending = list(_pending_delayed_tasks)
  del _pending_delayed_tasks[:]
  for t in old_pending:
    if not _main_loop_running:
      return
    if now >= t.run_at_or_after:
      try:
        t.cb()
      except KeyboardInterrupt:
        raise
      except:
        _on_exception()
    else:
      _pending_delayed_tasks.append(t)
  _pending_delayed_tasks.sort(lambda x, y: cmp(x, y))

def post_task(cb, *args):
  post_delayed_task(cb, 0, *args)

def post_delayed_task(cb, delay, *args):
  def on_run():
    cb(*args)
  _pending_delayed_tasks.append(DelayedTask(on_run, delay))
  _pending_delayed_tasks.sort(lambda x, y: cmp(x, y))

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
  return _main_loop_running

def run_main_loop():
  global _old_std
  _old_std = [ sys.stdout, sys.stderr ]

  if DEBUG:
    tempStdout = open('/tmp/quickopen.stdout', 'w', 0)
    sys.stdout = tempStdout
    sys.stderr = sys.stdout
  else:
    tempStdout = cStringIO.StringIO()
    sys.stdout = tempStdout
    sys.stderr = sys.stdout
  
  assert not is_main_loop_running()
  if _unittests_running and not _active_test:
    del _pending_delayed_tasks[:]
    del _quit_handlers[:]
    raise Exception("UITestCase must be used for tests that use the message_loop.")

  global _main_loop_running
  global _stdscr
  global _quitting

  def main(stdscr):
    global _stdscr
    _stdscr = stdscr
    while _main_loop_running:
      now = time.time()
      if len(_pending_delayed_tasks) > 0:
        delay = max(0, _pending_delayed_tasks[0].run_at_or_after - now)
      else:
        delay = 0.1
      try:
        r, w, e = select.select([sys.stdin], [], [], delay)
      except KeyboardInterrupt:
        raise
      except:
        continue

      if not _main_loop_running:
        break
      if r:
        if on_terminal_readable.has_listeners:
          on_terminal_readable.fire()
        else:
          print "unhandled character:", _stdscr.getch()
      _run_pending_tasks()
  try:
    _main_loop_running = True
    curses.wrapper(main)
  except KeyboardInterrupt:
    traceback.print_exc()
    raise
  except:
    traceback.print_exc()
  finally:
    _stdscr = None
    _quitting = False
    _main_loop_running = False
    del _pending_delayed_tasks[:]
    sys.stdout = _old_std[0]
    sys.stderr = _old_std[1]
    if DEBUG:
      tempStdout.close()
      res = open('/tmp/quickopen.stdout')
      sys.stdout.write(res.read())
      res.close()
    else:
      sys.stdout.write(tempStdout.getvalue())

def quit_main_loop():
  global _quitting
  if _quitting:
    return
  _quitting = True

  def do_quit():
    for cb in _quit_handlers:
      cb()
    del _quit_handlers[:]

    global _main_loop_running
    _main_loop_running = False

  post_task(do_quit)
