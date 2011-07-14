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
import glib
import gtk
import re
import time
import logging
import os

from info_bar_gtk import *

from open_dialog_base import OpenDialogBase

class OpenDialogGtk(gtk.Dialog, OpenDialogBase):
  def __init__(self, settings, db):
    gtk.Dialog.__init__(self)
    OpenDialogBase.__init__(self, settings, db)

    self.set_title("Quick open...")
    self.set_size_request(1000,400)
    self.add_button("_Open",gtk.RESPONSE_OK)
    self.add_button("Cancel",gtk.RESPONSE_CANCEL)

    model = gtk.ListStore(object)

    treeview = gtk.TreeView(model)
    treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
    treeview.get_selection().connect('changed', self._on_treeview_selection_changed)

    text_cell_renderer = gtk.CellRendererText()

    def add_column(title,accessor_cb):
      column = gtk.TreeViewColumn(title, text_cell_renderer)
      column.set_cell_data_func(text_cell_renderer, lambda column, cell, model, iter: cell.set_property('text', accessor_cb(model.get(iter,0)[0])))
      treeview.append_column(column)
      return column
    add_column("File",lambda obj: os.path.basename(obj))
    add_column("Path",lambda obj: os.path.dirname(obj))

    self.connect('destroy', self.on_destroy)

    truncated_bar = InfoBarGtk()
    refresh_button = gtk.Button("_Refresh")
    refresh_button.connect('clicked', lambda *args: self.refresh())

    reset_button = gtk.Button("Rese_t Database")
    reset_button.connect('clicked', lambda *args: self._reset_database())


    stats_label = gtk.Label()
#    def do_update_stats():
#      self._update_stats(stats_label)
#    glib.timeout_add(250, self._update_stats)

    filter_entry = gtk.Entry()
    filter_entry.set_text(self._filter_text)
    filter_entry.connect('key_press_event', self._on_filter_entry_keypress)
    filter_entry.connect('changed', self._on_filter_text_changed)

    # attach everything up
    vbox = self.vbox
    table_vbox = gtk.VBox()
    treeview_scroll_window = gtk.ScrolledWindow()
    treeview_scroll_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    table_options_hbox = gtk.HBox()
    button_hbox = gtk.HBox()

#    self.get_content_area().add(vbox)
    vbox.pack_start(table_vbox,True,True,1)
    table_vbox.pack_start(table_options_hbox,False,False,0)
    table_options_hbox.pack_start(reset_button,False,False,0)
    table_options_hbox.pack_start(stats_label,False,False,10)
    table_options_hbox.pack_end(refresh_button,False,False,0)
    table_vbox.pack_start(treeview_scroll_window,True,True,0)
    table_vbox.pack_start(truncated_bar,False,True,0)
    table_vbox.pack_start(filter_entry,False,True,0)
    treeview_scroll_window.add(treeview)
    vbox.show_all()

    truncated_bar.hide()

    # remember things that need remembering
    self._treeview = treeview
    self._model = model
    self._truncated_bar = truncated_bar

    filter_entry.grab_focus()

    self.refresh()

  def response(self, arg):
    self.just_before_closed()
    gtk.Dialog.response(self, arg)

  def on_destroy(self, *args):
    self.response(gtk.RESPONSE_CANCEL)

  def _on_filter_entry_keypress(self,entry,event):
    keyname = gtk.gdk.keyval_name(event.keyval)

    def redirect():
      prev = self.get_focus()
      self._treeview.grab_focus()
      ret = self._treeview.emit('key_press_event', event)
      if prev:
        prev.grab_focus()
      return True

    if keyname in ("Up", "Down", "Page_Up", "Page_Down", "Left", "Right"):
      return redirect()
    elif keyname == "space" and event.state & gtk.gdk.CONTROL_MASK:
      return redirect()
    elif keyname == "a" and event.state & gtk.gdk.CONTROL_MASK:
      return redirect()
    elif keyname == 'Return':
      self.response(gtk.RESPONSE_OK)

  def _on_filter_text_changed(self,entry):
    text = entry.get_text()
    self.set_filter_text(text)

#  def _update_stats(self,stats_label):
#    w = self._db.call_async_waitable.get_stats()
#    w.when_done(lambda v: stats_label.set_text(v))
#    return self.get_property('visible')

  def _reset_database(self):
    self._db.sync()
    self.refresh()

  def refresh(self):
    # TODO(nduca) save the selection
    if self._filter_text != "":
      ft = str(self._filter_text)
      res = self._db.search(ft)
      self.on_result(res)
    else:
      self._model.clear()

  # update the model based on result
  def on_result(self, files):
    start_time = time.time()
    self._treeview.freeze_child_notify()
    self._treeview.set_model(None)

    self._model.clear()

    for f in files:
      row = self._model.append()
      self._model.set(row, 0, f)

    self._treeview.set_model(self._model)
    self._treeview.thaw_child_notify()

    truncated = False
    if truncated:
      self._truncated_bar.text = "Search was truncated at %i items" % len(files)
      self._truncated_bar.show()
    else:
      self._truncated_bar.hide()

    elapsed = time.time() - start_time

    if len(self._model) > 0:
      if self._treeview.get_selection():
        self._treeview.get_selection().select_path((0,))

  def _on_treeview_selection_changed(self, selection):
    self.set_response_sensitive(gtk.RESPONSE_OK,selection.count_selected_rows() != 0)

  @property
  def selected_files(self):
    model,rows = self._treeview.get_selection().get_selected_rows()

    files = []
    for path in rows:
      iter = model.get_iter(path)
      obj = model.get(iter,0)[0]
      files.append(obj)
    return files

def run(settings, db):
  dlg = OpenDialogGtk(settings, db)
  resp = dlg.run()
  dlg.hide()
  if resp == gtk.RESPONSE_OK:
    print dlg.selected_files

if __name__ == "__main__":
  import db_test_base
  import settings
  import tempfile
  import temporary_daemon

  db_test_base = db_test_base.DBTestBase()
  db_test_base.setUp()
  daemon = temporary_daemon.TemporaryDaemon()
  client_settings_file = tempfile.NamedTemporaryFile()
  client_settings = settings.Settings(client_settings_file.name)
  db = daemon.db_proxy
  db.add_dir(db_test_base.test_data_dir)
  run(client_settings, db)
  db_test_base.tearDown()
  client_settings_file.close()
