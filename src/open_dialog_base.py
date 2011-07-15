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
# limitaions under the License.
import logging
import re

class OpenDialogBase(object):
  def __init__(self, settings, db):
    settings.register("filter_text", str, "")
    self._filter_text = settings.filter_text
    self._settings = settings
    self._db = db

  def just_before_closed(self):
    self._settings.filter_text = self._filter_text

  def set_filter_text(self, text):
    try:
      re.compile(text)
    except Exception, ex:
      logging.error("Regexp error: %s", str(ex))
    self._filter_text = text
    self.refresh()

  def rescan(self):
    self._db.sync()
    self.refresh()

  def refresh(self):
    # TODO(nduca) save the selection
    if self._filter_text != "":
      ft = str(self._filter_text)
      res = self._db.search(ft)
      self.update_results_list(res)
    else:
      self.update_results_list([])
