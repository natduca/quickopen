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

def _pick_open_dialog():
  assert message_loop.get_toolkit() != None
  module_name = 'src.open_dialog_%s' % message_loop.get_toolkit()
  class_name = 'OpenDialog%s' % message_loop.get_toolkit_class_suffix()
  module = __import__(module_name, {}, {}, True)
  return getattr(module, class_name)

OpenDialog = _pick_open_dialog()

def run(options, db, initial_filter, print_results_cb = None):
  def go():
    dlg = OpenDialog(options, db, initial_filter)
    if print_results_cb:
      dlg.print_results_cb = print_results_cb

  message_loop.post_task(go)
  message_loop.run_main_loop()
