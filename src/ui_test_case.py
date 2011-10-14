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
import message_loop
import os
import subprocess
import sys
import tempfile
import unittest

class UITestException(Exception):
  pass

class UITestCase(unittest.TestCase):
  def __init__(self, method_name, is_in_slave = False):
    unittest.TestCase.__init__(self, method_name)
    self._method_name = method_name
    self._is_in_slave = is_in_slave
    
  def run(self, result):
    if sys.platform == 'darwin' and '--objc' in sys.argv:
      if not self._is_in_slave:
        return self.run_darwin(result)
      else:
        assert message_loop.is_main_loop_running()
        message_loop.set_active_test(self, result)
        self.async_run_testcase(result)
    else:
      def do_test():
        self.async_run_testcase(result)
      message_loop.post_task(do_test)
      message_loop.set_active_test(self, result)
      message_loop.run_main_loop()
      message_loop.set_active_test(None, None)
      
  def async_run_testcase(self, result):
    result.startTest(self)
    testMethod = getattr(self, self._method_name)
    self._num_failures_at_start = len(result.failures)
    self._num_errors_at_start = len(result.errors)

    try:
      self.setUp()
    except KeyboardInterrupt:
      raise
    except:
      result.addError(self, self._exc_info())
      self.async_teardown_and_stop_test(result,tearDown=False)
      return

    ok = False
    try:
      testMethod()
      ok = True
    except self.failureException:
      result.addFailure(self, self._exc_info())
      self.async_teardown_and_stop_test(result)
    except KeyboardInterrupt:
      self.async_teardown_and_stop_test(result)
      raise
    except:
      result.addError(self, self._exc_info())
      self.async_teardown_and_stop_test(result)

    def do_async_teardown_and_stop_test():
      self.async_teardown_and_stop_test(result)
    message_loop.add_quit_handler(do_async_teardown_and_stop_test)


  def async_teardown_and_stop_test(self, result, tearDown=True):
    try:
      if len(result.failures) == self._num_failures_at_start and len(result.errors) == self._num_errors_at_start:
        result.addSuccess(self)
      
      if tearDown:
        try:
          self.tearDown()
        except KeyboardInterrupt:
          raise
        except:
          result.addError(self, self._exc_info())
          ok = False
          if ok: result.addSuccess(self)
    finally:
       result.stopTest(self)
       message_loop.quit_main_loop()


  def run_darwin(self, testResult):
    mod = __import__(self.__class__.__module__, {},{},fromlist=[True])
    # if this pops, then your test class wasn't on the module, which is required for this test system
    try:
      cls = getattr(mod, self.__class__.__name__) 
    except AttributeError:
      raise AttributeError("Your class must be a member of the enclosing module %s." % self.__class__.__module__)
    assert cls == self.__class__

    result = tempfile.NamedTemporaryFile()
    basedir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))
    quickopen_stub_app = os.path.join(basedir, "./support/quickopen_stub.app/Contents/MacOS/quickopen_stub")
    args = [quickopen_stub_app,
            "--main-name", "src.ui_test_case",
            "--module", self.__class__.__module__,
            "--class", self.__class__.__name__,
            "--method", self._method_name,
            "--result", result.name]
    if '--objc' in sys.argv:
      args.append('--objc')
    self._slave_proc = subprocess.Popen(args, cwd=basedir)

    # todo, add timeout...
    try:
      self._slave_proc.wait()
    finally:
      if self._slave_proc.poll() == None:
        self._slave_proc.kill()

    f = open(result.name, 'r')
    r = f.read()
    f.close()
    result.close()

    if not len(r):
      childTestResult = {
          "testsRun": 1,
          "errors": ["Target crashed!"],
          "failures": [],
          "shouldStop": False}
    else:
      try:
        childTestResult = eval(r)
      except:
        print "could not eval [%s]" % r
        raise
    testResult.startTest(self)
    for e in childTestResult["errors"]:
      try:
        raise UITestException(e)
      except:
        testResult.addError(self, sys.exc_info())
    for e in childTestResult["failures"]:
      try:
        raise UITestException(e)
      except:
        testResult.addFailure(self, sys.exc_info())

    if len(childTestResult["failures"]) == 0 and len(childTestResult["errors"]) == 0:
      testResult.addSuccess(self)

    if childTestResult["shouldStop"]:
      testResult.stop()
    testResult.stopTest(self)
    
def main_usage():
  return "Usage: %prog"

def main(parser):
  parser.add_option("--module", dest="module")
  parser.add_option("--class", dest="cls")
  parser.add_option("--method", dest="method")
  parser.add_option("--result", dest="result")
  (options, args) = parser.parse_args()
  
  mod = __import__(options.module, {},{},fromlist=[True])
  cls = getattr(mod, options.cls)
  test = cls(options.method, is_in_slave = True)
  result = unittest.TestResult()
  _output_ran = []
  def output_result():
    f = open(options.result, 'w')
    s = repr({
      "testsRun": result.testsRun,
      "errors": [e for t,e in result.errors],
      "failures": [e for t,e in result.failures],
      "shouldStop": result.shouldStop})
    f.write(s)
    f.close()
    _output_ran.append(True)
  message_loop.add_quit_handler(output_result)
  def do_test():
    message_loop.set_unittests_running(True)
    test.run(result)
  message_loop.post_task(do_test)
  message_loop.run_main_loop()
