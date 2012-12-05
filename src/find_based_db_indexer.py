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
import fnmatch
import logging
import math
import os
import re
import select
import subprocess
import tempfile
import time

from src import db_indexer
from trace_event import *

LINES_TO_READ_PER_SELECT = 1000

def _MakeIgnorePredicate(ignores):
  def is_ignored(filename):
    for i in ignores:
      if fnmatch.fnmatch(filename, i):
        return True
    return False
  return is_ignored

"""
_BasenameLevelFilter takes a fully qualified filename and splitting it on
separators. E.g.:
   foo/bar/baz.txt -> [foo, bar, baz.txt]

It then tests whether a given predicate matches any of those basenames,
memoizing the results to minimize calls to the predicate.
"""
class _BasenameLevelFilter(object):
  def __init__(self, basename_predicate):
    self._basename_predicate = basename_predicate
    self._cached_predicate_results = dict()

  def match_filename(self, filename):
    basenames = filename.split(os.sep)
    for basename in basenames:
      x = self._cached_predicate_results.get(basename)
      if x == None:
        x = self._basename_predicate(basename)
        self._cached_predicate_results[basename] = x

      if x:
        return True
    return False


"""
a/b/c/x.txt -> filter("a/b/c/x.txt"), filter("a/b/c"), filter("a/b"), filter("a") -> False
   set prefix to a/b/c since thats the last one that caused it to True

a/b/c/d -> False
a/b/d -> filter("a/b/d") -> True
"""
class _DirectoryLevelFilter(object):
  def __init__(self, filename_predicate):
    self._filename_predicate = filename_predicate
    self._current_matched_prefix = None

  def match_filename(self, filename):
    # Slow path.
    if False:
      return self._filename_predicate(filename)

    if (self._current_matched_prefix and
        filename.startswith(self._current_matched_prefix)):
      return True

    if not self._filename_predicate(filename):
      return False

    # Now, figure out the part that matched
    last_matching_pefix = filename
    remaining_parts = filename.split(os.sep)
    while len(remaining_parts) > 1:
      possibly_matching_prefix = os.sep.join(remaining_parts)
      if self._filename_predicate(possibly_matching_prefix):
        last_matching_pefix = possibly_matching_prefix
        remaining_parts = remaining_parts[1:]
        continue
      break

    # Store this, and quick-reject any filenames that
    # start with this prefix.
    self._current_matched_prefix = last_matching_pefix
    return True

def _get_filename_relative_to_find_dir(current_find_dir, filename):
  i = filename.find(current_find_dir)
  if i != 0:
    return filename
  subdir_with_slash = filename[len(current_find_dir):]
  return subdir_with_slash[1:]

def _IsProcessRunnable(name):
  try:
    with open(os.devnull, 'w') as devnull:
      found = subprocess.call(['/usr/bin/which', name],
                              stdout=devnull, stderr=devnull) == 0
      return True
  except OSError:
    return False

def Supported():
  return _IsProcessRunnable('/usr/bin/find')

class FindBasedDBIndexer(db_indexer.DBIndexer):
  def __init__(self, dirs, ignores):
    super(FindBasedDBIndexer, self).__init__(dirs)
    assert Supported()

    self._init_ignores(ignores)

    self._found_files = set()
    self._remaining_dirs = [
      os.path.realpath(d)
      for d in dirs]
    self._remaining_dirs.reverse()
    self._num_files_found = 0

    self._current_devnull = None
    self._current_find_dir = None
    self._current_find_subprocess = None
    self._lines_needing_processing = None
    self._find_results_tempfile = None

  def _init_ignores(self, ignores):
    self._dirname_ignores = []
    self._basename_ignores = []
    for i in ignores:
      if i.find(os.path.sep) != -1:
        self._dirname_ignores.append(i)
        continue
      self._basename_ignores.append(i)

  @property
  def progress(self):
    notes = ['%i files found' % self._num_files_found]
    if self._find_results_tempfile:
      st = os.stat(self._find_results_tempfile.name)
      size_in_kb = st.st_size / 1000.0
      rounded_size_in_kb = math.floor(size_in_kb * 100) / 100.0
      notes.append("%i kb of directories pending" % rounded_size_in_kb)
    notes.append(
      '%i toplevel dirs still to be indexed' % len(self._remaining_dirs))
    return '; '.join(notes)

  def index_a_bit_more(self):
    if self._lines_needing_processing:
      self._process_a_few_more_lines()
      return

    if not self._current_find_subprocess:
      logging.debug('Finding another dir to search.')
      self._begin_searching_next_dir()

    if self._current_find_subprocess:
      start = time.time()
      done = False
      while not done:
        time.sleep(0.1)
        if time.time() - start >= 0.20:
          break
        done = self._current_find_subprocess.poll() != None
      if not done:
        return

      logging.debug('Find finished.')
      trace_begin("read")
      with open(self._find_results_tempfile.name, 'r') as f:
        lines = f.readlines()
      trace_end("read")
      self._did_finish_searching_dir()
      if len(lines) > 0:
        logging.debug('Beginning to process lines.')
        self._lines_needing_processing = lines

    if (not self._current_find_subprocess and
        self._lines_needing_processing == None and
        len(self._remaining_dirs) == 0):
      logging.debug('Done.')
      self.complete = True

  @tracedmethod
  def _begin_searching_next_dir(self):
    if len(self._remaining_dirs) == 0:
      return

    dirname = self._remaining_dirs[0]
    self._remaining_dirs = self._remaining_dirs[1:]

    full_args = ['/usr/bin/find',
                 '-H', # Make find report the destination of symlinks.
                 dirname,
                 '-type', 'f']
    self._find_results_tempfile = tempfile.NamedTemporaryFile()
    self._current_devnull = open(os.devnull, 'w')
    logging.debug('Running %s' % ' '.join(full_args))
    self._current_find_dir = dirname
    self._current_find_subprocess = subprocess.Popen(
      full_args,
      stdout=self._find_results_tempfile,
      stderr=self._current_devnull)

  def _did_finish_searching_dir(self):
    self._find_results_tempfile.close()
    self._find_results_tempfile = None

    self._current_find_subprocess.wait()
    self._current_find_subprocess = None

    self._current_devnull.close()
    self._current_devnull = None

  def _process_a_few_more_lines(self):
    assert self._current_find_dir != None
    NUM_LINES_PER_STEP = 5000

    lines = self._lines_needing_processing[:NUM_LINES_PER_STEP]
    self._lines_needing_processing = self._lines_needing_processing[NUM_LINES_PER_STEP:]

    self._process_lines(self._current_find_dir, lines)

    if len(self._lines_needing_processing) == 0:
      logging.debug('Done processing lines.')
      self._current_find_dir = None
      self._lines_needing_processing = None

  @tracedmethod
  def _process_lines(self, current_find_dir, lines):
    dlf = _DirectoryLevelFilter(_MakeIgnorePredicate(self._dirname_ignores))
    blf = _BasenameLevelFilter(_MakeIgnorePredicate(self._basename_ignores))
    for line in lines:
      filename = line.strip()

      if filename in self._found_files:
        continue
      self._found_files.add(filename)

      dirname, basename = os.path.split(filename)
      _, ext = os.path.splitext(basename)
      relative_filename = _get_filename_relative_to_find_dir(current_find_dir, filename)
      if dlf.match_filename(filename):
        continue
      if blf.match_filename(relative_filename):
        continue

      if basename not in self.files_by_basename:
        self.files_by_basename[basename] = []
      self.files_by_basename[basename].append(filename)

      self._num_files_found += 1
