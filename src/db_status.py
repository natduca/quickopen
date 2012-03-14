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
class DBStatus(object):
  def __init__(self):
    self.is_up_to_date = False
    self.has_index = False
    self.status = "Unknown"
    self.running = True

  def as_dict(self):
    return {"is_up_to_date": self.is_up_to_date,
            "has_index": self.has_index,
            "status": self.status,
            "running": self.running }

  @staticmethod
  def not_running_string():
    return "quickopend not running"

  @staticmethod
  def not_running():
    s = DBStatus()
    s.status = DBStatus.not_running_string()
    return s

  @staticmethod
  def from_dict(d):
    s = DBStatus()
    s.is_up_to_date = d["is_up_to_date"]
    s.has_index = d["has_index"]
    s.status = d["status"]
    s.running = d["running"]
    return s
