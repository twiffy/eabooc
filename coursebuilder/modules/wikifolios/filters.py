#!/usr/bin/env python
import jinja2
from google.appengine.api.app_identity import get_application_id
import urllib

def student_link_for_admins(author, text=None):
    '''
    Create a link to the wikifolio page of the author.

    The text is the author's name unless you specify it.
    '''
    linked_name = jinja2.Markup(
            '<a href="wikiprofile?student=%(id)s">%(text)s</a> (%(email)s)')
    if not text:
        text = author.name

    return linked_name % {
            'id': author.wiki_id,
            'text': text,
            'email': author.key().name(),
            }

def student_link(author, text=None):
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


def dark_magic_db_edit_href(key):
    root = 'https://appengine.google.com/datastore/edit'
    params = {
            'app_id': get_application_id(),
            'key': key,
            }
    return root + '?' + urllib.urlencode(params)


