/* Copyright (c) 2012 The Chromium Authors. All rights reserved.
 * Use of this source code is governed by a BSD-style license that can be
 * found in the LICENSE file.
 */
'use strict';

(function() {
  var db_host;
  var db_port;

  function Query(text) {
    this.text = text,
    this.max_hits = 100;
    this.exact_match = false;
    this.current_filename = undefined;
    this.open_filenames = [];
    this.debug = false;
  }

  function reqAsync(method, path, data, response_cb, opt_err_cb) {
    var url = 'http://' + db_host + ':' + db_port + path;
    var req = new XMLHttpRequest();
    req.open(method, url, true);
    req.addEventListener('load', function() {
      if (req.status == 200)
        return response_cb(JSON.parse(req.responseText));
      if (opt_err_cb)
        opt_err_cb();
      else
        console.log('reqAsync ' + url, req);
    });
    req.addEventListener('error', function() {
      if (opt_err_cb)
        opt_err_cb();
      else
        console.log('reqAsync ' + url, req);
    });
    if (data)
      req.send(JSON.stringify(data));
    else
      req.send(null);
  }

  function $(sel) {
    return document.querySelector(sel);
  }


  chromeapp.addEventListener('launch', init);

  function init(launch_event) {
    assert(launch_event.args[0] == '--host');
    db_host = launch_event.args[1];
    assert(launch_event.args[2] == '--port');
    db_port = launch_event.args[3];
    var initial_filter = launch_event.args[4];

    $('#input').tabIndex = 1;
    $('#ok-button').tabIndex = 2;
    $('#cancel-button').tabIndex = 3;
    $('#bad-result-button').tabIndex = 4;
    $('#refresh-button').tabIndex = 5;
    $('#status-text').textContent = 'Hello world';

    $('#input').textContent = initial_filter;
    $('#input').addEventListener('change', onInputChanged);
    $('#input').addEventListener('input', onInputChanged);
    $('#input').addEventListener('keydown', function(e) {
      if (e.keyCode == 13) {
        onOkClicked();
      } else if (e.keyCode == 27) {
        onCancelClicked();
      } else if (e.keyCode == 38) { // up
        $('#results').moveSelection(-1);
        e.preventDefault();
      } else if (e.keyCode == 40) { // down
        $('#results').moveSelection(1);
        e.preventDefault();
      } else if (e.ctrlKey && e.keyCode == 78) { // C-n
        $('#results').moveSelection(1);
        e.preventDefault();
      } else if (e.ctrlKey && e.keyCode == 80) { // C-pf
        $('#results').moveSelection(-1);
        e.preventDefault();
      }
    }.bind(this));

    $('#ok-button').addEventListener('click', onOkClicked);
    $('#cancel-button').addEventListener('click', onCancelClicked);

    chrome.app.window.current().onClosed.addListener(onCancelClicked);
    chrome.app.window.current().focus();

    document.addEventListener('focusin', function() {
      if (document.activeElement == document.body) {
        setTimeout(function() {
          $('#input').focus();
        }, 0);
      }
    });
    document.addEventListener('keydown', function(e) {
      if (e.keyCode == 9 &&
          e.shiftKey) {
        if (e.target == $('#input')) {
          e.preventDefault();
          setTimeout(function() {
            $('#refresh-button').focus();
          }, 0);
        }
      }
    });

    ResultsTable.decorate($('#results'));

    setInterval(beginUpdateStatus, 250);
  }

  var updateStatusPending = false;
  function beginUpdateStatus() {
    if (updateStatusPending)
      return;

    reqAsync('GET', '/status', undefined, function(status) {
      updateStatusPending = false;
      $('#status-text').textContent = status.status;
    }, function() {
      updateStatusPending = false;
      $('#status-text').textContent = 'quickopend not running';
    });
  }

  function onOkClicked() {
    if ($('#results').selected_hit === undefined)
      return;

    // If a search is pending then hold until query comes back.
    if (searchPending) {
      searchPendingCallback = onOkClicked;
      return;
    }

    chromeapp.sendEvent('results', [$('#results').selected_hit], false);
    chromeapp.exit(0);
  }

  function onCancelClicked() {
    chromeapp.sendEvent('results', [], true);
    chromeapp.exit(1);
  }

  function updateResults(results) {
    $('#results').results = results;
  }

  var searchPending = false;
  var searchPendingCallback = undefined;

  function onInputChanged() {
    var text = $('#input').value;
    if (searchPending)
      return;
    var query = new Query(text);
    searchPending = true;
    reqAsync('POST', '/search', query, function(results) {
      searchPending = false;
      updateResults(results);
      if ($('#input').value != text)
        onInputChanged();
      if (searchPendingCallback) {
        searchPendingCallback();
        searchPendingCallback = undefined;
      }
    }, function() {
      searchPending = false;
      updateResults(undefined);
      if (searchPendingCallback) {
        searchPendingCallback();
        searchPendingCallback = undefined;
      }
    });
  }

  function assert(bool) {
    if (bool)
      return;
    throw new Error("Expected true");
  }

})();
