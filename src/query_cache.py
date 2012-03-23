# Copyright 2012 Google Inc.
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
import fixed_size_dict

class QueryCache(object):
  """Cached query execution results."""
  def __init__(self):
    self.searches = fixed_size_dict.FixedSizeDict(256)

  def try_get(self, query):
    qkey = query.text + "@%i" % query.max_hits
    if qkey in self.searches:
      return self.searches[qkey]
    return None

  def put(self, query, res):
    qkey = query.text + "@%i" % query.max_hits
    self.searches[qkey] = res
