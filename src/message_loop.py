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
import sys

_toolkit = None
_initialized = False
_platform_message_loop = None

TOOLKIT_GTK = 'gtk'
TOOLKIT_WX = 'wx'
TOOLKIT_OBJC = 'objc'
TOOLKIT_CURSES = 'curses'
TOOLKIT_CHROME = 'chrome'

def _initialize_if_needed():
  global _initialized
  if _initialized:
    return
  _initialized = True

  _detect_toolkit()

  global _platform_message_loop
  module_name = 'src.message_loop_%s' % _toolkit
  _platform_message_loop = __import__(module_name, {}, {}, True)

def _detect_toolkit():
  global _toolkit
  # use curses if its specified
  if '--curses' in sys.argv:
    _toolkit = TOOLKIT_CURSES
    return

  # use chrome if specified
  if '--chrome' in sys.argv:
    _toolkit = TOOLKIT_CHROME
    return

  # check whether we even have X
  if os.getenv('DISPLAY'):
    can_have_gui = True
  elif sys.platform == 'darwin':
    can_have_gui = True
  else:
    can_have_gui = False

  # Try using chrome.
  if can_have_gui:
    import message_loop_chrome
    if message_loop_chrome.supported():
      _toolkit = TOOLKIT_CHROME
      return

  # try using PyObjC on mac
  if sys.platform == 'darwin':
    if '--objc' in sys.argv:
      try:
        import objc
        _toolkit = TOOLKIT_OBJC
        return
      except ImportError:
        pass

  # try using gtk
  if can_have_gui:
    try:
      import pygtk
      pygtk.require('2.0')
      _toolkit = TOOLKIT_GTK
      return
    except ImportError:
      pass

  # if that didn't work, try using wx
  if can_have_gui:
    try:
      import wx
      _toolkit = TOOLKIT_WX
      return
    except ImportError:
      if sys.platform == 'darwin':
        sys.stderr.write("""You could have a nice pretty WxWidgets-based UI!

1. Download wxpython 2.9 Cocoa for python 2.7: http://downloads.sourceforge.net/wxpython/wxPython2.9-osx-2.9.5.0-cocoa-py2.7.dmg
2. Mount the image (double click the downloaded .dmg file)
3. Open a Terminal window, and run the following:
   sudo installer -pkg /Volumes/wxPython2.9-osx-2.9.5.0-cocoa-py2.7/wxPython2.9-osx-cocoa-py2.7.pkg  -target /

""")

  # use curses as a last resort
  if '--curses' in sys.argv or not can_have_gui:
    _toolkit = TOOLKIT_CURSES
    return

  _toolkit = None

def supports_prelaunch():
  # This function is called on the prelaunch hotpath. Thus, it needs to avoid importing things like gtk or wx,
  # which are what necessitate prelaunching in the first place.
  if '--curses' in sys.argv:
    return False

  # use chrome if specified
  if '--chrome' in sys.argv:
    return False

  # check whether we even have X
  if os.getenv('DISPLAY'):
    pass
  elif sys.platform == 'darwin':
    pass
  else:
    return False

  # Try using chrome.
  import message_loop_chrome
  if message_loop_chrome.supported():
    return False

  return True

def get_toolkit():
  _initialize_if_needed()
  return _toolkit

def get_toolkit_class_suffix():
  _initialize_if_needed()
  return _toolkit[0].upper() + _toolkit[1:]

def post_task(cb, *args):
  _initialize_if_needed()
  _platform_message_loop.post_task(cb, *args)

def post_delayed_task(cb, delay, *args):
  _initialize_if_needed()
  _platform_message_loop.post_delayed_task(cb, delay, *args)

def is_main_loop_running():
  _initialize_if_needed()
  return _platform_message_loop.is_main_loop_running()

def init_main_loop():
  _initialize_if_needed()
  _platform_message_loop.init_main_loop()

def run_main_loop():
  """
  Runs the main loop. Note, this is not guaranteed to return on all platforms.
  You should never call this in unit tests --- if you have a test that requires
  UI or that wants to do asynchronous tests, derive from UITestcase which will
  call this for you.
  """
  _initialize_if_needed()
  _platform_message_loop.run_main_loop()

def add_quit_handler(cb):
  _initialize_if_needed()
  _platform_message_loop.add_quit_handler(cb)

def quit_main_loop():
  """
  Tries to quit the main loop. Note, think of this as quitting the application,
  not quitting the loop and returning to the run_main_loop caller. This is how a
  sane operating system works. However, this code works on OSX.
  """
  _initialize_if_needed()
  _platform_message_loop.quit_main_loop()

def set_unittests_running(running):
  _initialize_if_needed()
  _platform_message_loop.set_unittests_running(running)

def set_active_test(test, result):
  _initialize_if_needed()
  _platform_message_loop.set_active_test(test, result)

def ensure_has_message_loop():
  _initialize_if_needed()
  if not _toolkit:
    supports = ['PyGtk', 'WxPython', 'Curses']
    if '--objc' in sys.argv:
      supports.append('PyObjC')
    print """No supported GUI toolkit found. Trace_event_viewer supports %s.""" % ", ".join(supports)
    sys.exit(255)
