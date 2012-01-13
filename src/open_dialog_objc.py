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
import time
import logging
import message_loop
import os
import sys

import objc
from AppKit import *
from Foundation import *

from open_dialog import OpenDialogBase

class OpenDialogObjcRaw(NSObject, OpenDialogBase):
  def initWithSettings(self, settings, options, db, initial_filter):
    message_loop.init_main_loop()
    self.init()
    OpenDialogBase.__init__(self, settings, options, db, initial_filter)

    size = NSMakeRect(0,0,800,400)
    self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
      size,
      NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask | NSMiniaturizableWindowMask,
      NSBackingStoreBuffered,
      False)
    self.window.setTitle_("TraceViewer")
    self.window.contentView().setAutoresizesSubviews_(True)

    ok_bn = NSButton.new()
    ok_bn.setTitle_("OK")
    ok_bn.setFrame_(NSMakeRect(100,100,200,50))
    ok_bn.setBezelStyle_(NSRoundedBezelStyle)
    ok_bn.setTarget_(self)
    ok_bn.setAction_(self.__class__.on_ok)

    cancel_bn = NSButton.new()
    cancel_bn.setTitle_("CANCEL")
    cancel_bn.setFrame_(NSMakeRect(100,100,200,50))
    cancel_bn.setBezelStyle_(NSRoundedBezelStyle)
    cancel_bn.setTarget_(self)
    cancel_bn.setAction_(self.__class__.on_cancel)

    

    self.window.contentView().addSubview_(ok_bn)

    self.window.makeKeyAndOrderFront_(self)
    self.window.center()

    return self

  @objc.IBAction
  def on_ok(self, a):
    print "ok"
    return

  def destroy(self):
    pass

  def set_status(self,status_text):
    pass

  def set_results_enabled(self,en):
    pass

  def update_results_list(self, files, ranks):
    pass

  def get_selected_items(self):
    raise Exception("Not implemented")

  def windowWillClose_(self, notification):
    print "foo"
    app.terminate_(self)

# Method that instantiates OpenDialogObjc class using alloc().init()
def OpenDialogObjc(*args):
  o = OpenDialogObjcRaw.alloc().initWithSettings(*args)
  return o
