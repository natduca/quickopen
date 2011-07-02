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
class DB(object):
  def __init__(self, settings):
    self.settings_ = settings

  def on_bound_to_server(sever):
    server.add_json_route('/add_dir', self.add_dir)
    server.add_json_route('/list_dirs', self.list_dirs)

  def add_dir(self,dir):
    pass

  def list_dirs(self,query):
    return ["~/"]

  def search(self,query):
    return

  @property
  def settings(self):
    return self.settings_
