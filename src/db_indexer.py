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
import collections
import os
import time
import json

class DBIndexer(object):
  def __init__(self, dirs):
    self.dirs = dirs
    self.complete = False
    self.files_by_basename = dict()

  def progress(self):
    raise NotImplementedException()

def Create(dirs, dir_cache):
  import find_based_db_indexer
  if find_based_db_indexer.Supported():
    return find_based_db_indexer.FindBasedDBIndexer(
      dirs, dir_cache.ignores)

  import listdir_based_db_indexer
  return listdir_based_db_indexer.ListdirBasedDBIndexer(dirs, dir_cache)
