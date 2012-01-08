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
import db_index_shard
import unittest
import re

class DBIndexShardTest(unittest.TestCase):
  def test_filters(self):
    m = db_index_shard.DBIndexShard({})
    camelcase = m.get_camelcase_wordstart_filter
    delimited = m.get_delimited_wordstart_filter
    substring = m.get_substring_filter
    superfuzzy = m.get_superfuzzy_filter

    def check_match(getflt, example, query, expected):
      flt, case_sensitive = getflt(query)
      if not case_sensitive:
        example = example.lower()
      example = "\n%s\n" % example
      res = re.search(flt, example)
      self.assertEquals(res != None, expected)

    def ensure_matches(getflt, example, query):
      check_match(getflt, example, query, True)
    def ensure_nonmatch(getflt, example, query):
      check_match(getflt, example, query, False)

    # delimited tests
    ensure_matches (delimited, "render_widget_host", "rwh")
    ensure_matches (delimited, "render_widget_host", "r")
    ensure_matches (delimited, "render_widget_host", "wh")
    ensure_matches (delimited, "render_widget_host", "w")
    ensure_matches (delimited, "render_widget_host", "rw")
    ensure_matches (delimited, "render_widget_host", "rw")
    ensure_nonmatch(delimited, "render_widget_host", "rwhv") # /me wonders if this should match?
    ensure_nonmatch(delimited, "render_widget_host", "rhwv") # /me wonders if this should match?
    ensure_nonmatch(delimited, "RenderWidget", "rw")
    ensure_nonmatch(delimited, "RenderWidget", "rw")
    ensure_nonmatch(delimited, "RenderWidget", "rw")
    ensure_nonmatch(delimited, "foo", "_")

    # delimited tests
    ensure_matches (camelcase, "RenderWidgetHost", "rwh")
    ensure_matches (camelcase, "RenderWidgetHost", "rw")
    ensure_matches (camelcase, "RenderWidgetHost", "r")
    ensure_matches (camelcase, "RenderWidgetHost", "wh")
    ensure_matches (camelcase, "Render_Widget_Host", "r")
    ensure_matches (camelcase, "Render_Widget_Host", "rw")
    ensure_matches (camelcase, "Render_Widget_Host", "rwh")
    ensure_nonmatch(delimited, "render_widget", "ei")
    ensure_nonmatch(delimited, "foo_render_widget", "_")

    # substring tests
    ensure_matches (superfuzzy, "RenderWidgetHost", "ren")
    ensure_matches (superfuzzy, "RenderWidgetHost", "renderwidget")
    ensure_matches (superfuzzy, "RenderWidgetHost", "enderwidget")
    ensure_nonmatch(superfuzzy, "RenderWidgetHost", "renderview")

    # superfuzzy tests
    ensure_matches (superfuzzy, "RenderWidgetHost", "rwh")
    ensure_matches (superfuzzy, "RenderWidgetHost", "endgethost")
    ensure_matches (superfuzzy, "f*oo", "*")
    ensure_nonmatch(superfuzzy, "foo", "*")
    ensure_nonmatch(superfuzzy, "foo", "_")



  def test_wordstart_db_index_shard(self):
    m = db_index_shard.DBIndexShard({
        "render_widget_host.cpp": ["a/render_widget_host.cpp","b/render_widget_host.cpp"],
        "foo.cpp": ["foo.cpp"],
        "bar.cpp": ["bar.cpp"],
        })
    
    hits, truncated = m.search_basenames("rwh", 10000)
    self.assertTrue("render_widget_host.cpp" in hits)
