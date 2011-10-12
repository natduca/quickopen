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
import sys

if sys.platform != 'darwin':
  raise Exception("Only usable on darwin")

# This makes me throw up in my mouth. You will too, I suspect. And,
# hopefully, decide you're a better programmer than I, and make this all
# better. :)
#
# This bit of trickery is because I want the actual fact that quickopen
# commandline needs to use an App bundle to launch. But I can't, for the life of
# me, figure out how to boot an objc app up without a bundle.
#
# The first of this file is to create the 
# support/quickopen_stub app that we use to start the
# viewer.
#
# Then, we embed this file in that app, which will get called
# when the app launches. In that case, we call out to the src
# directory to get the actual UI going.
#
# Did that make you sick, too?

def try_to_exec_stub(main_name, tried_once=False):
  # If laucned via the command line, then we will looko for the stub and if
  # found, will run that instead, on the fervent hope that it will eventually
  # be kind enough to call src.__init__'s main()
  objc_found = False
  try:
    import objc
    objc_found = True
  except ImportError:
    pass
  if objc_found:
    import os
    basedir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    quickopen_stub_app = os.path.join(basedir, "./support/quickopen_stub.app/Contents/MacOS/quickopen_stub")
    if not os.path.exists(quickopen_stub_app):
      if tried_once:
        print "Warning: could not create the stub."
        return False

      import shutil
      if os.path.exists(os.path.join(basedir, "./support/quickopen_stub.app/")):
        shutil.rmtree(os.path.join(basedir, "./support/quickopen_stub.app/"))
      create_stub()
      return try_to_exec_stub(main_name, True)

    # look for the stub itself
    bootstrap_objc_py = os.path.join(basedir, "./support/quickopen_stub.app/Contents/Resources/bootstrap_objc.py")
    if not os.path.exists(bootstrap_objc_py):
      print "Warning: something is messed up with the ObjC stub. You should regenerate it with python -m src.bootstrap_objc"
      import shutil
      if os.path.exists(os.path.join(basedir, "./support/quickopen_stub.app/")):
        shutil.rmtree(os.path.join(basedir, "./support/quickopen_stub.app/"))
      create_stub()
      return try_to_exec_stub()

    # Found the stub, but is the stub's copy of bootstrap_objc this one?
    # TODO: what we probably should do is point the bundle's stub at this via symlink
    this_stub = os.path.splitext(__file__)[0] + '.py'
    if os.stat(bootstrap_objc_py).st_mtime < os.stat(this_stub).st_mtime:
      print "Note: updating the stub's bootstrap_objc manually."
      import shutil
      shutil.copyfile(this_stub, bootstrap_objc_py)

    # look for the nib itself and make sure its updated
    bootstrap_nib = os.path.join(basedir, "./support/quickopen_stub.app/Contents/Resources/quickopen.nib")
    bootstrap_nib_designable = os.path.join(bootstrap_nib, "designable.nib")
    if not os.path.exists(bootstrap_nib_designable):
      raise "Critical failure looking for the nib"
    this_nib = os.path.join(basedir, "./src/quickopen.nib")
    this_nib_designable = os.path.join(this_nib, "designable.nib")
    if os.stat(bootstrap_nib_designable).st_mtime < os.stat(this_nib_designable).st_mtime:
      print "Note: updating the stub's nib manually."
      import shutil
      shutil.rmtree(bootstrap_nib)
      shutil.copytree(this_nib, bootstrap_nib)

    # execv over to the stub... this python smelled funny, anyway.
    argv = [quickopen_stub_app, "--main-name", main_name]
    argv.extend(sys.argv[1:])
    os.execv(quickopen_stub_app, argv)

def is_inside_stub_bundle():
  # Assume we were launched inside a bundle
  import Foundation
  b = Foundation.NSBundle.mainBundle()
  bname = b.infoDictionary()["CFBundleName"]
  return b.infoDictionary()["CFBundleName"] == 'quickopen_stub'

def create_stub():
  # If you run setup using /usr/bin, py2app will assume that we want python's environment
  # to be based out of /usr/local. This, of course, is disastrous because the resulting
  # app wont be able to find PyObjC. The solution is to re-launch python in a more "official"
  # place that won't make py2app cry.
  if sys.executable.startswith("/usr"):
    py = "/System/Library/Frameworks/Python.framework/Versions/Current/bin/python"
    import os
    if not os.path.exists(py):
      raise Exception("Coudln't find python")
    args = [py]
    args.extend(sys.argv)
    os.execv(py, args)

  import os
  basedir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
  os.chdir(basedir)

  from distutils.core import setup
  import py2app

  print "Creating quickopen_stub... please be patient..."
  setup(
    script_args=["py2app"],
    name="quickopen_stub",
    app=['./src/bootstrap_objc.py'],
    data_files=["./src/quickopen.nib"],
    options={
      "py2app": {
        "dist_dir": "./support",
        "plist": {
          "NSMainNibFile": "quickopen",
        },
        "semi_standalone": True,
        "site_packages": True,
        "excludes": "wx"
      }
    }
  )

def run_real_main():
  import os
  basedir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../"))
  os.chdir(basedir)
  
  if sys.argv[1] != '--main-name':
    raise Exception("Do not launch this stub directly.")

  assert os.path.exists(os.path.join(basedir, "src/__init__.py"))
  sys.path.append(basedir)
  bootstrap = __import__("src.bootstrap", {}, {}, True) # do this to prevent disttools from discovering this dependency!!
  try:
    bootstrap.run()
  except KeyboardInterrupt:
    import traceback
    traceback.print_exc()
    sys.exit(255)

if __name__ == "__main__":
  if is_inside_stub_bundle():
    run_real_main()
  else:
    create_stub()
