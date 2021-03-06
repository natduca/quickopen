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
import time
import logging
import os

from info_bar_gtk import *

from open_dialog_base import OpenDialogBase

class OpenDialogGtk(gtk.Dialog, OpenDialogBase):
  def __init__(self, options, db, initial_filter):
    gtk.Dialog.__init__(self)
    OpenDialogBase.__init__(self, options, db, initial_filter)

    self.set_title("Quick open...")
    self.set_size_request(1000,400)
    self.add_button("_Open",gtk.RESPONSE_OK)
    self.add_button("Cancel",gtk.RESPONSE_CANCEL)

    model = gtk.ListStore(object)

    treeview = gtk.TreeView(model)
    treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
    treeview.get_selection().connect('changed', self._on_treeview_selection_changed)

    self.connect('response', self.response)

    text_cell_renderer = gtk.CellRendererText()

    def add_column(title,accessor_cb):
      column = gtk.TreeViewColumn(title, text_cell_renderer)
      column.set_cell_data_func(text_cell_renderer, lambda column, cell, model, iter: cell.set_property('text', accessor_cb(model.get(iter,0)[0])))
      treeview.append_column(column)
      return column
    add_column("Rank",lambda obj: obj[1])
    add_column("File",lambda obj: os.path.basename(obj[0]))
    add_column("Path",lambda obj: os.path.dirname(obj[0]))

    self.connect('destroy', self.on_destroy)

    truncated_bar = InfoBarGtk()

    bad_result_button = gtk.Button("Bad result")
    bad_result_button.connect('clicked', lambda *args: self.on_badresult_clicked())

    reindex_button = gtk.Button("_Reindex")
    reindex_button.connect('clicked', lambda *args: self.on_reindex_clicked())

    status_label = gtk.Label()
    self.status_label = status_label

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

    vbox.pack_start(table_vbox,True,True,1)
    table_vbox.pack_start(table_options_hbox,False,False,0)
    table_options_hbox.pack_start(status_label,False,False,10)
    table_options_hbox.pack_end(bad_result_button,False,False,0)
    table_options_hbox.pack_end(reindex_button,False,False,0)
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
    self._filter_entry = filter_entry

    filter_entry.grab_focus()
    if self.should_position_cursor_for_replace:
      filter_entry.set_position(0)
      filter_entry.select_region(0, len(self._filter_text))
    else:
      filter_entry.set_position(len(self._filter_text))

    self.show_all()

  def response(self, arg, *rest):
    canceled = len(rest) > 0 and rest[0] != gtk.RESPONSE_OK
    self.on_done(canceled)

  def on_destroy(self, *args):
    self.response(None, gtk.RESPONSE_CANCEL)

  def redirect_to_treeview(self, event):
    prev = self.get_focus()
    self._treeview.grab_focus()
    ret = self._treeview.emit('key_press_event', event)
    if prev:
      prev.grab_focus()
    return True

  def _on_filter_entry_keypress(self,entry,event):
    keyname = gtk.gdk.keyval_name(event.keyval)

    if keyname in ("Up", "Down", "Page_Up", "Page_Down", "Left", "Right"):
      return self.redirect_to_treeview(event)
    elif keyname == "space" and event.state & gtk.gdk.CONTROL_MASK:
      return self.redirect_to_treeview(event)
    elif keyname == 'n' and event.state & gtk.gdk.CONTROL_MASK:
      self.move_selection(1)
      return True
    elif keyname == 'p' and event.state & gtk.gdk.CONTROL_MASK:
      self.move_selection(-1)
      return True
    elif keyname == 'a' and event.state & gtk.gdk.CONTROL_MASK:
      i = self._filter_entry.set_position(0)
      return True
    elif keyname == 'e' and event.state & gtk.gdk.CONTROL_MASK:
      self._filter_entry.set_position(len(self._filter_entry.get_text()))
      return True
    elif keyname == 'f' and event.state & gtk.gdk.CONTROL_MASK:
      i = self._filter_entry.get_position()
      i = min(i + 1, len(self._filter_entry.get_text()))
      self._filter_entry.set_position(i)
      return True
    elif keyname == 'b' and event.state & gtk.gdk.CONTROL_MASK:
      i = self._filter_entry.get_position()
      if i >= 1:
        self._filter_entry.set_position(i - 1)
      return True
    elif keyname == 'k' and event.state & gtk.gdk.CONTROL_MASK:
      i = self._filter_entry.get_position()
      t = self._filter_entry.get_text()[:i]
      self._filter_entry.set_text(t)
      self._filter_entry.set_position(len(t))
      return True
    elif keyname == 'Return':
      self.response(gtk.RESPONSE_OK)
      return True

  def _on_filter_text_changed(self,entry):
    text = entry.get_text()
    self.set_filter_text(text)

  def set_results_enabled(self, en):
    self._treeview.set_sensitive(en)
    self.set_response_sensitive(gtk.RESPONSE_OK, en)

  def status_changed(self):
    self.status_label.set_text(self.status_text)

  # update the model based on result
  def update_results_list(self, files, ranks):
    if len(files) == 0:
      self._model.clear()
      return

    start_time = time.time()
    self._treeview.freeze_child_notify()
    self._treeview.set_model(None)

    self._model.clear()

    for i in range(len(files)):
      row = self._model.append()
      self._model.set(row, 0, (files[i], ranks[i]))

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

  def move_selection(self, direction):
    sel = self.get_selected_indices()
    if len(sel) == 0:
      if self._model.iter_n_children(None) == 0:
        return
      self.set_selected_indices([0])
      return

    if direction > 0:
      i = max(sel)
    else:
      i = min(sel)
    i = i + direction
    if i < 0:
      return
    if i >= self._model.iter_n_children(None):
      return
    self.set_selected_indices([i])

  def get_selected_indices(self):
    model,rows = self._treeview.get_selection().get_selected_rows()
    return [x[0] for x in rows]

  def set_selected_indices(self, indices):
    sel = self._treeview.get_selection()
    for i in self.get_selected_indices():
      sel.unselect_path((i,))
    for i in indices:
      sel.select_path((i,))

  def get_selected_items(self):
    model,rows = self._treeview.get_selection().get_selected_rows()

    files = []
    for path in rows:
      iter = model.get_iter(path)
      obj = model.get(iter,0)[0][0]
      files.append(obj)
    return files
