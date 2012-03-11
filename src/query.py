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

class Query(object):
  """Encapsulates all the options to Quickopen search system."""

  @staticmethod
  def from_kargs(args = [], kwargs = {}):
    """A wrapper for old mechanisms of implicitly constructing queries."""
    if len(args) == 1:
      if isinstance(args[0], Query):
        return args[0]
      else:
        return Query(*args, **kwargs)        
    else:
      return Query(*args, **kwargs)

  def __init__(self, text, max_hits = 100, exact_match = False, current_filename = None, open_filenames = []):
    self.text = text
    self.max_hits = max_hits
    self.exact_match = exact_match
    self.current_filename = current_filename
    self.open_filenames = open_filenames

  @staticmethod
  def from_dict(d):
    return Query(d["text"],
                 d["max_hits"],
                 d["exact_match"],
                 d["current_filename"],
                 d["open_filenames"])

  def as_dict(self):
    return {
      "text": self.text,
      "max_hits": self.max_hits,
      "exact_match": self.exact_match,
      "current_filename": self.current_filename,
      "open_filenames": self.open_filenames
      }

