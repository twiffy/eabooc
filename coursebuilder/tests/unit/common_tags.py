# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for common.tags."""

__author__ = 'John Orr (jorr@google.com)'

import unittest
from xml.etree import cElementTree
from common import tags


class CustomTagTests(unittest.TestCase):
    """Unit tests for the custom tag functionality."""

    def setUp(self):

        class SimpleTag(tags.BaseTag):
            def render(self, unused_arg):
                return cElementTree.Element('SimpleTag')

        class ComplexTag(tags.BaseTag):
            def render(self, unused_arg):
                return cElementTree.XML(
                    '<Complex><Child>Text</Child></Complex>')

        class ReRootTag(tags.BaseTag):
            def render(self, node):
                elt = cElementTree.Element('Re')
                root = cElementTree.Element('Root')
                elt.append(root)
                for child in node:
                    root.append(child)
                return elt

        def new_get_tag_bindings():
            return {
                'simple': SimpleTag,
                'complex': ComplexTag,
                'reroot': ReRootTag}

        self.old_get_tag_bindings = tags.get_tag_bindings
        tags.get_tag_bindings = new_get_tag_bindings

    def tearDown(self):
        tags.get_tag_bindings = self.old_get_tag_bindings

    def test_empty_text_is_passed(self):
        safe_dom = tags.html_to_safe_dom(None)
        self.assertEquals('', str(safe_dom))

    def test_none_is_treated_as_empty(self):
        safe_dom = tags.html_to_safe_dom(None)
        self.assertEquals('', str(safe_dom))

    def test_plain_text_is_passed(self):
        safe_dom = tags.html_to_safe_dom('This is plain text.')
        self.assertEquals('This is plain text.', str(safe_dom))

    def test_mix_of_plain_text_and_tags_is_passed(self):
        html = 'This is plain text<br/>on several<br/>lines'
        safe_dom = tags.html_to_safe_dom(html)
        self.assertEquals(html, str(safe_dom))

    def test_simple_tag_is_replaced(self):
        html = '<div><simple></simple></div>'
        safe_dom = tags.html_to_safe_dom(html)
        self.assertEquals('<div><SimpleTag></SimpleTag></div>', str(safe_dom))

    def test_replaced_tag_preserves_tail_text(self):
        html = '<div><simple></simple>Tail text</div>'
        safe_dom = tags.html_to_safe_dom(html)
        self.assertEquals(
            '<div><SimpleTag></SimpleTag>Tail text</div>', str(safe_dom))

    def test_simple_tag_consumes_children(self):
        html = '<div><simple><p>child1</p></simple></div>'
        safe_dom = tags.html_to_safe_dom(html)
        self.assertEquals(
            '<div><SimpleTag></SimpleTag></div>', str(safe_dom))

    def test_complex_tag_preserves_its_own_children(self):
        html = '<div><complex/></div>'
        safe_dom = tags.html_to_safe_dom(html)
        self.assertEquals(
            '<div><Complex><Child>Text</Child></Complex></div>', str(safe_dom))

    def test_reroot_tag_puts_children_in_new_root(self):
        html = '<div><reroot><p>one</p><p>two</p></reroot></div>'
        safe_dom = tags.html_to_safe_dom(html)
        self.assertEquals(
            '<div><Re><Root><p>one</p><p>two</p></Root></Re></div>',
            str(safe_dom))

    def test_chains_of_tags(self):
        html = '<div><reroot><p><simple></p></reroot></div>'
        safe_dom = tags.html_to_safe_dom(html)
        self.assertEquals(
            '<div><Re><Root><p><SimpleTag></SimpleTag></p></Root></Re></div>',
            str(safe_dom))

    def test_scripts_are_not_escaped(self):
        html = '<script>alert("2"); var a = (1 < 2 && 2 > 1);</script>'
        safe_dom = tags.html_to_safe_dom(html)
        self.assertEquals(html, str(safe_dom))

