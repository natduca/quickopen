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
import settings
import tempfile
import unittest

class SettingsTest(unittest.TestCase):
  def test_basic(self):
    f = tempfile.NamedTemporaryFile()
    s = settings.Settings(f.name)
    self.assertFalse(s.has_setting("foo"))
    self.assertRaises(settings.SettingDoesntExistException,lambda: s["foo"])
    s.register("doSomething",bool,True)
    self.assertTrue(s.has_setting("doSomething"))
    self.assertFalse(s.is_manually_set("doSomething"))
    self.assertTrue(s["doSomething"])
    self.assertTrue(s.doSomething)
    self.assertRaises(Exception,lambda: s.register("doSomething",int,None)) # type mismatch
    self.assertRaises(TypeError,lambda: s.set("doSomething","Foo"))
    self.assertRaises(settings.SettingDoesntExistException,lambda: s.set("bar","boo"))

    # change the setting manually to false...
    s.set("doSomething",False)
    self.assertEqual(s.doSomething,False)
    self.assertTrue(s.is_manually_set("doSomething"))

    # check that this was saved and persisted...
    s2 = settings.Settings(f.name)
    s2.register("doSomething",bool,True)
    self.assertFalse(s2.doSomething)
    self.assertTrue(s2.is_manually_set(s2.doSomething))
    f.close()

  def test_has_unresolved(self):
    f = tempfile.NamedTemporaryFile()
    t = open(f.name,"w")
    t.write("""{"foo" : True}""")
    t.close()
    s = settings.Settings(f.name)
    self.assertTrue(s.has_unresolved_settings())
    f.close()

  def test_from_existing(self):
    f = tempfile.NamedTemporaryFile()
    t = open(f.name,"w")
    t.write("""{"foo" : "Bar"}""")
    t.close()

    s = settings.Settings(f.name)
    s.register("foo",str,"")
    self.assertFalse(s.has_unresolved_settings())
    self.assertTrue(s.is_manually_set("foo"))
    self.assertEqual(s.foo,"Bar")
    f.close()

  def test_from_existing_with_type_mismatch(self):
    f = tempfile.NamedTemporaryFile()
    t = open(f.name,"w")
    t.write("""{"foo" : 3}""")
    t.close()

    s = settings.Settings(f.name)
    s.register("foo",str,"")
    self.assertFalse(s.has_unresolved_settings())
    self.assertFalse(s.is_manually_set("foo"))
    self.assertEqual(s.foo,"")
    f.close()

  def test_temporaries(self):
    f = tempfile.NamedTemporaryFile()
    t = open(f.name,"w")
    t.write("""{"foo" : "bar"}""")
    t.close()

    s = settings.Settings(f.name)
    s.register("foo",str,"default")
    s.register("bar",str,"default")
    s.set("foo","notdefault")
    self.assertEqual(s.foo, "notdefault")
    s.set_temporarily("foo","temporary")
    self.assertEqual(s.foo, "temporary")

    self.assertTrue(s.is_manually_set, "foo")
    self.assertTrue(s.is_manually_set, "bar")

    s.set_temporarily("bar","temporary")

    # ensure the file didn't change
    s2 = settings.Settings(f.name)
    s2.register("foo",str,"default")
    self.assertEqual(s2.foo,"notdefault")

    f.close()

  def test_dup_setting_that_matches_succeeds(self):
    f = tempfile.NamedTemporaryFile()
    s = settings.Settings(f.name)
    s.register("foo",int,3)
    s.register("foo",int,3)
    f.close()

  def test_register_with_mismatch_type_and_default(self):
    f = tempfile.NamedTemporaryFile()
    s = settings.Settings(f.name)
    self.assertRaises(Exception, lambda: s.register("foo",str,3))
    f.close()
    
  # tests for the change_fn feature
  def test_register_empty_doesnt_fire_change(self):
    f = tempfile.NamedTemporaryFile()
    s = settings.Settings(f.name)
    def on_change(old,new):
      raise Exception("Should never get called")
    s.register("foo",int,3,on_change)
    f.close()

  def test_register_nonempty_doesnt_fire_change(self):
    f = tempfile.NamedTemporaryFile()
    t = open(f.name,"w")
    t.write("""{"foo" : True}""")
    t.close()

    s = settings.Settings(f.name)
    def on_change(old,new):
      raise Exception("Should never get called")
    s.register("foo",int,3,on_change)
    f.close()

  def test_changing_empty_fires_change(self):
    f = tempfile.NamedTemporaryFile()
    s = settings.Settings(f.name)
    def on_change(old,new):
      self.assertEquals(3, old)
      self.assertEquals(4, new)
    s.register("foo",int,3,on_change)
    s.foo = 4
    f.close()

  def test_changing_setting_from_File(self):
    f = tempfile.NamedTemporaryFile()
    t = open(f.name,"w")
    t.write("""{"foo" : 3}""")
    t.close()
    s = settings.Settings(f.name)
    fired = [False]
    def on_change(old,new):
      self.assertEquals(3, old)
      self.assertEquals(4, new)
      fired[0] = True
    s.register("foo",int,3,on_change)
    s.foo = 3
    self.assertFalse(fired[0])
    s.foo = 4
    self.assertTrue(fired[0])
    f.close()

