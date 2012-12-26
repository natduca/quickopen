
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
_pending_tasks = []
_quit_handlers = []

def post_task(cb, *args):
  _pending_tasks.append({
      "cb": cb,
      "args": args})

def post_delayed_task(cb, delay, *args):
  raise NotImplementedException()

def is_main_loop_running():
  return False

def init_main_loop():
  raise NotImplementedException()

def run_main_loop():
  global _pending_tasks
  while len(_pending_tasks):
    t = _pending_tasks[0]
    _pending_tasks = _pending_tasks[1:]
    t["cb"](*t["args"])

  global _quit_handlers
  for cb in _quit_handlers:
    cb()
  _quit_handlers = []

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

