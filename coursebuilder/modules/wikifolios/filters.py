#!/usr/bin/env python
import jinja2

def author_link(author, text=None):
    '''
    Create a link to the wikifolio page of the author.

    The text is the author's name unless you specify it.
    '''
    linked_name = jinja2.Markup(
            '<a href="wikiprofile?student=%(id)s">%(text)s</a>')
    if not text:
        text = author.name

    return linked_name % {
            'id': author.wiki_id,
            'text': text,
            }

