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
from cStringIO import StringIO

# Pyton-serial object notation
class PSONException(Exception):
  def __init__(self,message):
    self._message = message
  @property
  def message(self):
    return self._message
  def __str__(self):
    return "%s" % self._message

def loads(str):
  return eval(str, {}, {})


###########################################################################
def _dumps_flat(obj):
  if obj == None:
    return "None"
  if isinstance(obj,list):
    return "[%s]" % ", ".join([_dumps_flat(c) for c in obj])
  elif isinstance(obj,dict):
    rows = ["\"%s\" : %s" % (key,_dumps_flat(obj[key])) for key in obj.keys()]
    return "{%s}" % ", ".join(rows)
  elif isinstance(obj,bool):
    if obj:
      return "True"
    else:
      return "False"
  elif isinstance(obj,float):
    return "%f" % obj
  elif isinstance(obj,int):
    return "%i" % obj
  elif isinstance(obj,str):
    return "\"%s\"" % obj
  else:
    raise PSONException("Unrecognized type %s" % type(obj))


###########################################################################
def _s(i):
  return "".ljust(i*4)
def _issimple(obj):
  if isinstance(obj,list) or isinstance(obj,dict):
    if len(obj) > 1:
      return False
    elif len(obj) == 1:
      if isinstance(obj,list):
        return _issimple(obj[0])
      else:
        return _issimple(obj.values()[0])
    else:
      return True
  else:
    return True

def _dumps_pretty(i,obj):
  if obj == None:
    return "None"
  if isinstance(obj,list):
    if _issimple(obj):
      return _dumps_flat(obj)
    
    s = StringIO()
    s.write("[\n")
    for j in range(len(obj)):
      s.write(_s(i+1))
      s.write(_dumps_pretty(i+1, obj[j]))
      if j < len(obj) - 1:
        s.write(",\n")
      else:
        s.write("\n")
    s.write(_s(i))
    s.write("]")

    return s.getvalue()
  elif isinstance(obj,dict):
    if _issimple(obj):
      return _dumps_flat(obj)

    s = StringIO()
    s.write("{\n")
    keys = obj.keys()
    keys.sort()
    for j in range(len(keys)):
      k = keys[j]
      v = obj[k]
      s.write(_s(i+1))
      s.write('"%s" : ' % k)
      s.write(_dumps_pretty(i+1, v))
      if j < len(obj) - 1:
        s.write(",\n")
      else:
        s.write("\n")
    s.write(_s(i))
    s.write("}")

    return s.getvalue()
  elif isinstance(obj,bool):
    if obj:
      return "True"
    else:
      return "False"
  elif isinstance(obj,float):
    return "%f" % obj
  elif isinstance(obj,int):
    return "%i" % obj
  elif isinstance(obj,basestring):
    return "\"%s\"" % obj
  else:
    raise PSONException("Unrecognized type %s" % type(obj))

###########################################################################

def dumps(obj,pretty=False):
  if pretty:
    return _dumps_pretty(0,obj)
  else:
    return _dumps_flat(obj)
def load(f):
  contents = f.read()
  return loads(contents)
def dump(obj):
  pson = dumps(obj)
  f.write(pson)
