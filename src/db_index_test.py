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
import db_index
import db_indexer
import sys
import unittest
import time

FILES_BY_BASENAME = None

class DBIndexTest(unittest.TestCase):
  def setUp(self):
    mock_indexer = db_indexer.MockIndexer('test_data/cr_files_by_basename_five_percent.json')
    self.index = db_index.DBIndex(mock_indexer)

  def test_case_sensitive_query(self):
    self.assertTrue('~/chrome/src/third_party/tlslite/tlslite/integration/ClientHelper.py' in self.index.search('ClientHelper').hits)

  def test_case_insensitive_query(self):
    self.assertTrue("~/ndbg/quickopen/src/db_proxy_test.py" in self.index.search('db_proxy_test').hits)

  def test_case_query_with_extension(self):
    self.assertTrue("~/ndbg/quickopen/src/db_proxy_test.py" in self.index.search('db_proxy_test.py').hits)
    self.assertTrue('~/chrome/src/third_party/tlslite/tlslite/integration/ClientHelper.py' in self.index.search('ClientHelper.py').hits)

  def test_dir_query(self):
    # should probably veirfy that 
    src = self.index.search('src').hits
    self.assertEquals([u'~/chrome/src/third_party/WebKit/LayoutTests/scrollbars/scrollbar-gradient-crash-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/qt/editing/style/style-boundary-004-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/editing/style/style-boundary-004-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/gtk/editing/style/style-boundary-004-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-win/editing/style/style-boundary-004-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-linux/editing/style/style-boundary-004-expected.png', u'~/chrome/src/third_party/WebKit/Source/WebCore/storage/StorageNamespace.cpp', u'~/chrome/src/third_party/WebKit/LayoutTests/svg/dynamic-updates/SVGFEMorphologyElement-svgdom-radius-call.html', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/preloader/scan-body-from-head-import-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/fast/repaint/search-field-cancel-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/gtk/fast/repaint/search-field-cancel-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-win/fast/repaint/search-field-cancel-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/css/space-before-charset.html', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/StorageNamespaceProxy.h', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/events/shadow-boundary-crossing.html', u'~/chrome/src/third_party/mesa/MesaLib/src/mesa/swrast/s_clear.c', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac-leopard/fast/inline/styledEmptyInlinesWithBRs-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/fast/inline/styledEmptyInlinesWithBRs-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/gtk/fast/inline/styledEmptyInlinesWithBRs-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-win/fast/inline/styledEmptyInlinesWithBRs-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-linux/fast/inline/styledEmptyInlinesWithBRs-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/forms/state-save-of-detached-control-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac-leopard/svg/dynamic-updates/SVGFECompositeElement-svgdom-in-prop-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/svg/dynamic-updates/SVGFECompositeElement-svgdom-in-prop-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/gtk/svg/dynamic-updates/SVGFECompositeElement-svgdom-in-prop-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-win/svg/dynamic-updates/SVGFECompositeElement-svgdom-in-prop-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-mac-leopard/svg/dynamic-updates/SVGFECompositeElement-svgdom-in-prop-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-mac/svg/dynamic-updates/SVGFECompositeElement-svgdom-in-prop-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-linux/svg/dynamic-updates/SVGFECompositeElement-svgdom-in-prop-expected.png', u'~/chrome/src/third_party/WebKit/Source/WebCore/svg/SVGForeignObjectElement.idl', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/table/section-in-table-before-misnested-text-crash.xhtml', u'~/chrome/src/third_party/WebKit/LayoutTests/storage/domstorage/localstorage/storagetracker/storage-tracker-1-prepare.html', u'~/chrome/src/crypto/symmetric_key_nss.cc', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/events/scroll-to-anchor-in-overflow-hidden.html', u'~/chrome/src/third_party/WebKit/Source/WebCore/svg/SVGAnimatedRect.h', u'~/chrome/src/third_party/WebKit/LayoutTests/svg/W3C-SVG-1.1-SE/struct-use-14-f.svg', u'~/chrome/src/third_party/mesa/MesaLib/src/gallium/drivers/i915/i915_surface.c', u'~/chrome/src/chrome/browser/autofill/form_structure_unittest.cc', u'~/chrome/src/chrome/test/data/extensions/api_test/tabs/capture_visible_tab/test_race.html', u'~/chrome/src/net/http/url_security_manager.cc', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/qt/css2.1/20110323/absolute-replaced-width-050-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/css2.1/20110323/absolute-replaced-width-050-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/gtk/css2.1/20110323/absolute-replaced-width-050-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-win/css2.1/20110323/absolute-replaced-width-050-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-mac-leopard/css2.1/20110323/absolute-replaced-width-050-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-linux/css2.1/20110323/absolute-replaced-width-050-expected.png', u'~/chrome/src/third_party/WebKit/Source/WebKit/chromium/src/WorkerFileWriterCallbacksBridge.cpp', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/css/import-and-insert-rule-no-update-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/qt/fast/css/focus-ring-multiline-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/fast/css/focus-ring-multiline-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/gtk/fast/css/focus-ring-multiline-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-win/fast/css/focus-ring-multiline-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-mac-leopard/fast/css/focus-ring-multiline-expected.txt', u'~/chrome/src/third_party/WebKit/Source/WebCore/platform/network/ResourceResponseBase.cpp', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/compositing/reflections/nested-reflection-anchor-point-expected.txt', u'~/chrome/src/third_party/launchpad_translations/generated_resources_ku.xtb', u'~/chrome/src/third_party/WebKit/LayoutTests/http/tests/appcache/destroyed-frame-expected.txt', u'~/chrome/src/chrome/browser/history/text_database_manager_unittest.cc', u'~/chrome/src/third_party/WebKit/LayoutTests/dom/xhtml/level3/core/typeinfoisderivedfrom19-expected.txt', u'~/chrome/src/chrome/browser/automation/automation_browser_tracker.cc', u'~/chrome/src/third_party/WebKit/Source/WebCore/platform/graphics/qt/TransformationMatrixQt.cpp', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/dom/Window/attr-constructor-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac-leopard/fast/forms/textarea-placeholder-set-attribute-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/fast/forms/textarea-placeholder-set-attribute-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/gtk/fast/forms/textarea-placeholder-set-attribute-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-win/fast/forms/textarea-placeholder-set-attribute-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-linux/fast/forms/textarea-placeholder-set-attribute-expected.png', u'~/chrome/src/third_party/WebKit/Source/JavaScriptCore/API/JSObjectRef.cpp', u'~/chrome/src/third_party/WebKit/LayoutTests/dom/xhtml/level1/core/hc_characterdataindexsizeerrreplacedataoffsetnegative.xhtml', u'~/chrome/src/third_party/WebKit/LayoutTests/http/tests/security/resources/cross-origin-script.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/replaced/css-content-and-webkit-mask-box-image-crash-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/qt/svg/custom/dynamic-svg-document-creation-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/svg/custom/dynamic-svg-document-creation-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/gtk/svg/custom/dynamic-svg-document-creation-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-win/svg/custom/dynamic-svg-document-creation-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/text/justify-ideograph-vertical.html', u'~/chrome/src/third_party/WebKit/Source/WebCore/bindings/js/JSDOMFormDataCustom.cpp', u'~/chrome/src/third_party/WebKit/LayoutTests/http/tests/security/cross-frame-access-enumeration.html', u'~/chrome/src/third_party/WebKit/Source/WebCore/inspector/front-end/InspectorBackendStub.qrc', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac-leopard/http/tests/security/dataTransfer-set-data-file-url-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac-leopard/editing/pasteboard/dataTransfer-set-data-file-url-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/http/tests/security/dataTransfer-set-data-file-url-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/editing/pasteboard/dataTransfer-set-data-file-url-expected.png', u'~/chrome/src/third_party/WebKit/Source/WebKit2/Shared/Plugins/NPObjectMessageReceiver.messages.in', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/win/svg/W3C-I18N/tspan-dirRTL-ubOverride-in-rtl-context-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/svg/W3C-I18N/tspan-dirRTL-ubOverride-in-rtl-context-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/gtk/svg/W3C-I18N/tspan-dirRTL-ubOverride-in-rtl-context-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-win/svg/W3C-I18N/tspan-dirRTL-ubOverride-in-rtl-context-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-mac-leopard/svg/W3C-I18N/tspan-dirRTL-ubOverride-in-rtl-context-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-linux/svg/W3C-I18N/tspan-dirRTL-ubOverride-in-rtl-context-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/dom/constructors-overriding-expected.txt', u'~/chrome/src/third_party/WebKit/LayoutTests/svg/custom/path-getPresentationAttribute-crash-expected.txt', u'~/chrome/src/third_party/WebKit/Source/WebCore/html/canvas/CanvasPattern.cpp', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/mac/editing/inserting/insert-div-004-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-win/editing/inserting/insert-div-004-expected.png', u'~/chrome/src/third_party/WebKit/LayoutTests/platform/chromium-linux/editing/inserting/insert-div-004-expected.png', u'~/chrome/src/third_party/WebKit/Tools/WebKitAPITest/WebKitAPITestDebugCairoCFLite.vsprops', u'~/chrome/src/third_party/WebKit/LayoutTests/http/tests/security/contentSecurityPolicy/inline-style-attribute-blocked.html', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/dom/Range/range-insertNode-separate-endContainer.html', u'~/chrome/src/third_party/WebKit/Source/WebCore/accessibility/AccessibilityRenderObject.cpp', u'~/chrome/src/third_party/WebKit/LayoutTests/css2.1/20110323/absolute-non-replaced-height-012.htm', u'~/chrome/src/third_party/WebKit/LayoutTests/fast/parser/empty-text-resource-expected.txt', u'~/chrome/src/chrome/app/theme/browser_actions_overflow_win_p.png', u'~/chrome/src/net/proxy/init_proxy_resolver.cc', u'~/chrome/src/third_party/WebKit/LayoutTests/canvas/philip/tests/2d.fillStyle.get.semitransparent-expected.txt'], src)


  def test_emtpy_dir_query(self):
    self.assertEquals([], self.index.search('/').hits)

  def test_two_dir_query(self):
    self.assertTrue("~/ndbg/quickopen/src/db_proxy_test.py" in self.index.search('quickopen/src/').hits)

  def test_dir_and_name_query(self):
    self.assertTrue("~/ndbg/quickopen/src/db_proxy_test.py" in self.index.search('src/db_proxy_test.py').hits)

class DBIndexPerfTest():
  def __init__(self):
    matchers = db_index.matchers()
    self.indexers = {}
    for (mn, m) in matchers.items():
      self.indexers[mn] = db_index.DBIndex(mock_indexer, mn)

  def test_matcher_perf(self,max_hits):
    header_rec = ["  %15s "]
    header_data = ["query"]
    entry_rec = ["  %15s "]
    for mn in self.indexers.keys():
      header_rec.append("%10s")
      header_data.append(mn)
      entry_rec.append("%10.4f")
    print ' '.join(header_rec) % tuple(header_data)

    PERF_QUERIES = [
    'warmup',
      'r',
      'rw',
      'rwh',
      'rwhv',
      're',
      'ren',
      'rend',
      'rende',
      'render',
      'render_',
      'render_w',
      'render_wi',
      'render_widget',
      'iv',
      'info_view',
      'w',
      'we',
      'web',
      'webv',
      'webvi',
      'webvie',
      'webview',
      'wv',
      'wvi',
      'webgraphics'
    ]
    for q in QUERIES:
      entry_data = [q]
      for mn,i in self.indexers.items():
        start = time.time()
        i.search(q,max_hits)
        elapsed = time.time() - start
        entry_data.append(elapsed)
      print ' '.join(entry_rec) % tuple(entry_data)
      
if __name__ == '__main__':
  test = DBIndexPerfTest('test_data/cr_files_by_basename.json')
  print "Results for max=30:"
  test.test_matcher_perf(max_hits=30)
  print "\n"
