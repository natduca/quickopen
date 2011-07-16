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
import tempfile
import shlex
import subprocess

class TestData(object):
  def __init__(self):
    # create a directory hierarchy to do tests in
    self.test_data_dir = os.path.realpath(os.path.join(tempfile.gettempdir(), 'db_test'))
    if os.path.exists(self.test_data_dir):
      self.system('rm -rf %s' % self.test_data_dir)
    self.system('cp -r ./test_data/ %s' % self.test_data_dir)

    # dir symlink project1_symlink to project1
    src = os.path.join(self.test_data_dir, 'project1')
    dst = os.path.join(self.test_data_dir, 'project1_symlink')
    ret = self.system('ln -s %s %s' % (src, dst))
    assert ret == 0

    # file symlink something/foo.txt to project1/something/foo.txt
    src = os.path.join(self.test_data_dir, 'project1/foo.txt')
    dst = os.path.join(self.test_data_dir, 'something/foo.txt')
    ret = self.system('ln -s %s %s' % (src, dst))
    assert ret == 0

    # make a real git directory
    gitpath = os.path.join(self.test_data_dir, 'gitproj')
    oldcwd = os.getcwd()
    os.chdir(gitpath)
    ret = self.system('git init')
    ret = self.system('git add .')
    ret = self.system('git commit -m .')
    assert ret == 0
    os.chdir(oldcwd)

  def system(self, cmd):
    args = shlex.split(cmd)
    p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    p.communicate()
    return p.returncode
    
  def close(self):
    if os.path.exists(self.test_data_dir):
      self.system('rm -rf %s' % self.test_data_dir)

