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
import re
import time
import json

"""
This module is a simple set of benchmarks on matching performance that
were used to decide on how to implement the matching algorithm in db.py

This code isn't used by the quickopen runtime, rather just included for
reference if additonal performance tuning is desired.
"""


def main():
  files_by_basename = json.loads(open('test_data/cr_files_by_basename.json').read())
  files = list(files_by_basename.keys())
  files_unsplit = "\n" + "\n".join(files) + "\n"

  queries = [
    'rwhv',
    'r',
    're',
    'ren',
    'rend',
    'rende',
    'render',
    'render_',
    'render_w',
    'render_wi',
    'render_widget',
    'iv',
    'info_view',
    'webgraphics'
    ]
  print "%15s %10s %10s %10s %10s" % ("query", "fn", "fnfilt", "re", "re2")
  for q in queries:
    test(files, files_unsplit, q)

def test(files, files_unsplit, q):
  # fnmatch-based matching
  def fn_fuzz(x):
    tmp = []
    for i in range(len(x)):
      tmp.append(x[i])
    return "*%s*" % '*'.join(tmp)
  fn_filt = fn_fuzz(q)
  start = time.time()
  fn_hits = [f for f in files if fnmatch.fnmatch(f, fn_filt)]
  fn_elapsed = time.time() - start

  # fnmatch-based matching
  fn_filt = fn_fuzz(q)
  start = time.time()
  fnfilt_hits = fnmatch.filter(files, fn_filt)
  fnfilt_elapsed = time.time() - start
  
  # re-based matching
  def re_fuzz(x):
    tmp = []
    for i in range(len(x)):
      tmp.append(x[i])
    return ".*%s.*" % '.*'.join(tmp)
  re_filt = re.compile(re_fuzz(q))
  start = time.time()
  re_hits = [f for f in files if re_filt.search(f)]
  re_elapsed = time.time() - start

  # re-based matching, but on one huge string and re limited by \n-delimiters
  def re2_fuzz(x):
    tmp = []
    for i in range(len(x)):
      tmp.append(x[i])
    return "\n.*%s.*\n" % '.*'.join(tmp)
  re2_filt = re.compile(re2_fuzz(q))
  base = 0
  start = time.time()
  re2_hits = []
  while True:
    m = re2_filt.search(files_unsplit, base)
    if m:
      re2_hits.append(m.group(0)[1:-1])
      base = m.end() - 1
    else:
      break
  re2_elapsed = time.time() - start

  assert fn_hits == fnfilt_hits
  assert fnfilt_hits == re_hits
  if re_hits != re2_hits:
    import pdb; pdb.set_trace()
  
  print "%15s %10.4f %10.4f %10.4f %10.4f" % (q, fn_elapsed, fnfilt_elapsed, re_elapsed, re2_elapsed)


if __name__ == '__main__':
  main()
