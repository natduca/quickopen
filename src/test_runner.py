#!/usr/bin/env python
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
import fcntl
import fnmatch
import logging
import message_loop
import optparse
import os
import platform
import resource
import sys
import types
import traceback
import unittest

def _get_open_fds():
  fds = set()
  for fd in range(3,resource.getrlimit(resource.RLIMIT_NOFILE)[0]):
    try:
      flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    except IOError:
      continue
    fds.add(fd)
  return fds

class IncrementalTestRunner(unittest.TextTestRunner):
  def __init__(self, options):
    unittest.TextTestRunner.__init__(self)
    self.options = options

  def run(self, test):
    def run(result):
      self._pre_run_hook()
      test(result)
      self._post_run_hook(result, test)
    return unittest.TextTestRunner.run(self, run)

  def _pre_run_hook(self):
    if self.options.check_for_fd_leaks:
      global _before
      _before = _get_open_fds()

  def _post_run_hook(self, result, test):
    import gc
    gc.collect()

    if self.options.check_for_fd_leaks:
      global _before
      after = _get_open_fds()
      dif = after.difference(_before)
      if len(dif):
        try:
          raise Exception("FD leak: %s" % repr(dif))
        except:
          result.addError(test, sys.exc_info())

def filter_suite(suite, predicate):
  new_suite = unittest.TestSuite()
  for x in suite:
    if isinstance(x, unittest.TestSuite):
      subsuite = filter_suite(x, predicate)
      if subsuite.countTestCases() == 0:
        continue

      new_suite.addTest(subsuite)
      continue

    assert isinstance(x, unittest.TestCase)
    if predicate(x):
      new_suite.addTest(x)

  return new_suite


def discover(start_dir, pattern = "test*.py", top_level_dir = None):
  if hasattr(unittest.defaultTestLoader, 'discover'):
    return unittest.defaultTestLoader.discover(start_dir, pattern, top_level_dir)

  # TODO(nduca): Do something with top_level_dir non-None
  modules = []
  for (dirpath, dirnames, filenames) in os.walk(start_dir):
    for filename in filenames:
      if not filename.endswith(".py"):
        continue

      if not fnmatch.fnmatch(filename, pattern):
        continue

      if filename.startswith('.') or filename.startswith('_'):
        continue
      name,ext = os.path.splitext(filename)
      fqn = dirpath.replace('/', '.') + '.' + name

      # load the module
      try:
        module = __import__(fqn,fromlist=[True])
      except:
        print "While importing [%s]\n" % fqn
        traceback.print_exc()
        continue
      modules.append(module)

  loader = unittest.defaultTestLoader
  subsuites = []
  for module in modules:
    if hasattr(module, 'suite'):
      new_suite = module.suite()
    else:
      new_suite = loader.loadTestsFromModule(module)
    if new_suite.countTestCases():
      subsuites.append(new_suite)
  return unittest.TestSuite(subsuites)

def get_tests_from_suite(suite):
  tests = []
  for x in suite:
    if isinstance(x, unittest.TestSuite):
      tests.extend(get_tests_from_suite(x))
      continue
    tests.append(x)
  return tests

def main_usage():
  return "Usage: run_tests [options] [names of tests to run]"

def main(parser):
  parser.add_option('--debug', dest='debug', action='store_true', default=False, help='Break into pdb when an assertion fails')
  parser.add_option('-i', '--incremental', dest='incremental', action='store_true', default=False, help='Run tests one at a time.')
  parser.add_option('-s', '--stop', dest='stop_on_error', action='store_true', default=False, help='Stop running tests on error.')
  parser.add_option('-m', '--manually-handled-tests', dest='manual_handling_allowed', action='store_true', default=False, help='Only run tests flagged with a \'requires_manual_handling\' attribute.')
  parser.add_option('--check-for-fd-leaks', dest='check_for_fd_leaks', action='store_true', default=False, help='Checks for fd leaks after each test run.')
  (options, args) = parser.parse_args()

  # install hook on set_trace if --debug
  if options.debug:
    import exceptions
    class DebuggingAssertionError(exceptions.AssertionError):
      def __init__(self, *args):
        exceptions.AssertionError.__init__(self, *args)
        print "Assertion failed, entering PDB..."
        import pdb
        if hasattr(sys, '_getframe'):
          pdb.Pdb().set_trace(sys._getframe().f_back.f_back)
        else:
          pdb.set_trace()
    unittest.TestCase.failureException = DebuggingAssertionError

    def hook(*args):
      import traceback, pdb
      traceback.print_exception(*args)
      pdb.pm()
    sys.excepthook = hook

    try:
      import browser
      browser.debug_mode = True
    except:
      pass

  if options.check_for_fd_leaks and not options.incremental:
    print "--check-for-fd-leaks forces --incremental."
    options.incremental = True

  # make sure cwd is the base directory!
  os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

  def args_filter(test):
    if len(args) == 0:
      return True

    for x in args:
      if str(test).find(x) != -1:
        return True
    return False

  def manual_test_filter(test):
    module_name = test.__class__.__module__
    module = sys.modules[module_name]

    requires_manual_handling = False
    if hasattr(module, 'requires_manual_handling'):
      requires_manual_handling = module.requires_manual_handling
    if requires_manual_handling != options.manual_handling_allowed:
      return False
    return True

  def module_filename_filter(test):
    if test.__class__.__name__.startswith("_"):
      return False

    module_name = test.__class__.__module__
    module = sys.modules[module_name]
    if module.__file__.startswith("."):
      return False
    return True

  def test_filter(test):
    if not module_filename_filter(test):
      return False
    if not manual_test_filter(test):
      return False
    if not args_filter(test):
      return False
    return True

  all_tests_suite = discover("src", "*_test.py", ".")
  selected_tests_suite = filter_suite(all_tests_suite, test_filter)

  if not options.incremental:
    r = unittest.TextTestRunner()
    message_loop.set_unittests_running(True)
    res = r.run(selected_tests_suite)
    message_loop.set_unittests_running(False)
    if res.wasSuccessful():
      return 0
    return 255
  else:
    r = IncrementalTestRunner(options)
    message_loop.set_unittests_running(True)
    ok = True
    for t in get_tests_from_suite(selected_tests_suite):
      assert isinstance(t, unittest.TestCase)
      print '----------------------------------------------------------------------'
      print 'Running %s' % str(t)

      res = r.run(t)
      if not res.wasSuccessful():
        ok = False
        if options.stop_on_error:
          break
    message_loop.set_unittests_running(False)
    if ok:
      return 0
    return 255

