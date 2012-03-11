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
import unittest

from query import Query

class QueryTest(unittest.TestCase):
  def test_cons(self):
    Query("a")
    Query("a", 10)
    Query("a", 10, True)
    Query("a", 10, True, "blahblah")
    Query("a", 10, True, "blahblah", ["bar"])
  
  def test_to_and_from_dict(self):
    x = Query("a", 10, True, "blahblah", ["bar"])
    y = x.as_dict()
    z = Query.from_dict(y)

    self.assertEquals(x.text, z.text)
    self.assertEquals(x.max_hits, z.max_hits)
    self.assertEquals(x.exact_match, z.exact_match)
    self.assertEquals(x.current_filename, z.current_filename)
    self.assertEquals(x.open_filenames, z.open_filenames)
