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
import traceback
import types
import pickle

class Event(object):
  def __init__(self):
    self._listeners = []

  def add_listener(self,cb):
    self._listeners.append(cb)

  @property
  def has_listeners(self):
    return len(self._listeners)

  def remove_listener(self,cb):
    self._listeners.remove(cb)

  def __getstate__(self):
    return {}
  def __setstate__(self,d):
    self._listeners = []

  def fire(self,*args):
    return self._fire(False,args)

  def fire_silent(self,*args):
    return self._fire(True,args)

  def _fire(self,silent,args):
    last = None
    for cb in self._listeners:
      try:
        last = cb(*args)
      except Exception,e:
        if not silent:
          print "Error on callback:"
          traceback.print_stack()
          traceback.print_exc()
          print "\n\n"
    return last
