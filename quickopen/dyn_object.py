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
import json

class DynObject(object):
  """
  DynObject is a class that behaves more like a javascript ojbect, i.e. one to which you
  can add fields after-the-fact. It is particularly useful for ad-hoc data structures.

  d may be a dict or a json-formatted string
  """
  def __init__(self,d=None):
    if d and type(d) == dict:
      for k in d.keys():
        setattr(self,k,d[k])
    elif d and type(d) == str:
      o = json.loads(d)
      for k in o.keys():
        setattr(self,k,o[k])

  def as_dict(self):
    d = dict()
    for x in dir(self):
      if (not x.startswith('_')) and x not in DynObject.__dict__:
        d[x] = getattr(self,x)
    return d

  def as_json(self):
    return json.dumps(self.as_dict())

  def __str__(self):
    return str(self.as_dict())

  def __repr__(self):
    return repr(self.as_dict())

  def __getattr__(self,name):
    raise AttributeError("Object has no attribute %s" % name)

  def __setattr(self,name,val):
    setattr(self,name,val)
    return val
