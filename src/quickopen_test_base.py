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
import temporary_daemon
import unittest
import subprocess
import test_data
import time

class QuickopenTestBase(object):
  def setUp(self):
    self.test_data = test_data.TestData()

  def qo_and_split(self, *args):
    r = self.qo(*args)
    if r:
      return [x for x in r.split("\n") if len(x)]
    else:
      return None

  @property
  def test_data_dir(self):
    return self.test_data.test_data_dir

  def tearDown(self):
    self.test_data.close()
    
  def test_1_dir(self):
    x = self.qo("add",
                self.test_data_dir)
    self.assertEquals("", x)
    d = self.qo("dirs").split("\n")
    self.assertEquals([self.test_data_dir, ''], d)

  def test_2_dirs(self):
    d1 = os.path.join(self.test_data_dir, 'project1')
    d2 = os.path.join(self.test_data_dir, 'something')

    x = self.qo("add", d1)
    self.assertEquals("", x)

    x = self.qo("add", d2)
    self.assertEquals("", x)

    d = self.qo("dirs").split("\n")
    self.assertEquals([d1, d2, ''], d)

  def test_rmdir(self):
    d1 = os.path.join(self.test_data_dir, 'project1')
    d2 = os.path.join(self.test_data_dir, 'something')

    x = self.qo("add", d1)
    self.assertEquals("", x)

    x = self.qo("add", d2)
    self.assertEquals("", x)

    x = self.qo("rmdir", d1).strip()
    self.assertEquals("%s removed" % d1, x)

    d = self.qo("dirs").split("\n")
    self.assertEquals([d2, ''], d)

  def test_ignore(self):
    x = self.qo("add",
                self.test_data_dir)
    self._wait_for_up_to_date()

    orig = self.qo_and_split("ignores")

    res = self.qo_and_split("rawsearch", 'svn_should_not_show_up.txt')
    self.assertEquals(0, len(res))

    orig = self.qo_and_split("ignores")
    for i in orig:
      self.qo("unignore", i)
    self._wait_for_up_to_date()

    res = self.qo_and_split("rawsearch", 'svn_should_not_show_up.txt')
    self.assertEquals(1, len(res))

  def test_status(self):
    s = self.qo("status")
    self.assertTrue(s.startswith("up-to-date: "))

  def test_status_nodaemon(self):
    self.turn_off_daemon()
    s = self.qo("status")
    print s
    self.assertTrue(s.startswith("quickopend not running."))

  def _is_up_to_date(self):
    s = self.qo("status")
    if s.startswith("up-to-date: "):
      return True
    return False

  def _wait_for_up_to_date(self):
    # times out after 10ms
    utd = False
    for i in range(10):
      if self._is_up_to_date():
        utd = True
        break
      time.sleep(0.2)
    self.assertTrue(utd)

  def test_rawsearch(self):
    x = self.qo("add",
                self.test_data_dir)
    self.assertEquals("", x)

    self._wait_for_up_to_date()
    r = self.qo("rawsearch", "MySubSystem.c").split("\n")
    self.assertEquals([self.test_data.path_to("project1/MySubSystem.c"), ''], r)

  def test_rawsearch_with_rank(self):
    x = self.qo("add",
                self.test_data_dir)
    self.assertEquals("", x)
    self._wait_for_up_to_date()
    
    r = self.qo("rawsearch", "--show-rank", "MySubSystem.c").split("\n")
    self.assertEquals(["14," + self.test_data.path_to("project1/MySubSystem.c"), ''], r)
