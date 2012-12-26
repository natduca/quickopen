/* Copyright (c) 2012 The Chromium Authors. All rights reserved.
 * Use of this source code is governed by a BSD-style license that can be
 * found in the LICENSE file.
 */
'use strict';

(function() {
  function ResultsTable() {
    var el = document.createElement('div');
    ResultsTable.decorate(el);
    return el;
  }

  ResultsTable.decorate = function(el) {
    el.__proto__ = ResultsTable.prototype;
    el.decorate();
  };

  ResultsTable.prototype = {
    __proto__: HTMLDivElement.prototype,

    decorate: function(){
      this.results_ = undefined;
      this.selected_index_ = 0;
      this.updateContents_();
    },

    set results(results) {
      this.results_ = results;
      this.updateContents_();
    },

    get results() {
      return this.results_;
    },

    get hits() {
      if (!this.results)
        return [];
      return this.results["hits"];
    },

    get selected_hit() {
      if (this.selected_index_ <= this.hits.length)
        return this.hits[this.selected_index_][0];
      return undefined;
    },

    moveSelection: function(offset) {
      var new_index = this.selected_index_ + offset;
      if (new_index < 0) new_index = 0;
      if (new_index >= this.hits.length)
        new_index = this.hits.length - 1;
      var changed = this.selected_index_ != new_index;
      this.selected_index_ = new_index;
      if (changed)
        this.updateContents_();
      var selEl = this.querySelector('.selected');
      if (selEl)
        selEl.scrollIntoViewIfNeeded();
    },

    updateContents_: function() {
      if (this.results_ === undefined) {
        this.textContent = 'type to search';
        return;
      }

      this.textContent = '';

      var tableEl = document.createElement('table');
      tableEl.className = 'results-table';

      {
        var tr = document.createElement('tr');
        var c0 = document.createElement('td');
        var c1 = document.createElement('td');
        var c2 = document.createElement('td');
        c0.className = 'results-table-prio-column';
        c1.className = 'results-table-basename-column';
        c2.className = 'results-table-path-column';
        c0.textContent = 'Prio';
        c1.textContent = 'Name';
        c2.textContent = 'Path';

        tr.appendChild(c0);
        tr.appendChild(c1);
        tr.appendChild(c2);
        tableEl.appendChild(tr);
      }

      var hits = this.hits;
      for (var i = 0; i < hits.length; i++) {
        var hit = hits[i];

        var tr = document.createElement('tr');
        var c0 = document.createElement('td');
        var c1 = document.createElement('td');
        var c2 = document.createElement('td');

        c0.textContent = Math.floor(hit[1] * 10) / 10;

        var lastSlash = hit[0].lastIndexOf('/');
        var basename, path;
        if (lastSlash == -1) {
          path = '';
          basename = hit[0];
        } else {
          path = hit[0].slice(0, lastSlash);
          basename = hit[0].slice(lastSlash + 1);
        }
        c1.textContent = basename;
        c2.textContent = path;

        tr.appendChild(c0);
        tr.appendChild(c1);
        tr.appendChild(c2);

        if (i == this.selected_index_)
          tr.classList.add('selected');

        tableEl.appendChild(tr);
      }
      this.appendChild(tableEl);
    }
  };

  window.ResultsTable = ResultsTable;
})();