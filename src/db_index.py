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
import os
import fnmatch

from dyn_object import DynObject

class DBIndex(object):
  def __init__(self, indexer):
    self.matcher = FnMatcher(indexer.files_by_basename)

  def search(self, query):
    slashIdx = query.rfind('/')
    if slashIdx != -1:
      dirpart = query[:slashIdx]
      basepart = query[slashIdx+1:]
    else:
      dirpart = None
      basepart = query
    
    hits = []
    truncated = False
    if len(basepart):
      (hits, truncated) = self.matcher.search(basepart)
    else:
      hits = self.files

    if dirpart:
      reshits = []
      for path in hits:
        dirname = os.path.dirname(path)
        if dirname.endswith(dirpart):
          reshits.append(path)
      hits = reshits
        
    res = DynObject()
    res.hits = hits
    res.truncated = truncated
    return res
    

class FnMatcher(object):
  def __init__(self, files_by_basename):
    self.files_by_basename = []
    self.files = []
    self.files_associated_with_basename = []
    for basename,files_with_basename in files_by_basename.items():
      idx_of_first_file = len(self.files)
      self.files_by_basename.append(basename)
      self.files_associated_with_basename.append(idx_of_first_file)
      self.files_associated_with_basename.append(len(files_with_basename))
      self.files.extend(files_with_basename)

  def search(self, query):
    tmp = ['*']
    for i in range(len(query)):
      tmp.append(query[i])
    tmp.append('*')
    flt = '*'.join(tmp)
    
    truncated = False
    hits = []
    for i in range(len(self.files_by_basename)):
      x = self.files_by_basename[i]
      if fnmatch.fnmatch(x, flt):
        lo = self.files_associated_with_basename[2*i]
        n = self.files_associated_with_basename[2*i+1]
        hits.extend(self.files[lo:lo+n])
        if len(hits) > 100:
          truncated = True
          break
    return (hits, truncated)
