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
import sys
import message_loop
import chromeapp

class OpenDialogChrome():
  def __init__(self, options, db, initial_filter):
    manifest_file = os.path.join(os.path.dirname(__file__),
                                 'chrome_app', 'manifest.json')
    self.app = chromeapp.App('quickopen',
                             manifest_file)
    self.print_results_cb = None
    # This postTask is needed because OpenDialog's base class assigns
    # print_results_cb after we return from the constructor, assuming
    # that the message loop is running. Le sigh.
    message_loop.post_task(self.Run, options, db, initial_filter)

  def Run(self, options, db, initial_filter):
    if initial_filter == None:
      initial_filter = ""
    args = ['--host', db.host,
            '--port', db.port,
            initial_filter]
    def OnResults(args):
      hits, canceled = args
      if self.print_results_cb:
        self.print_results_cb(
          hits,
          canceled)

    with chromeapp.AppInstance(self.app, args) as app_instance:
      app_instance.AddListener('results', OnResults)
      return app_instance.Run()
