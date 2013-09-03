#!/usr/bin/env python
import wtforms as wtf
import bleach
from jinja2 import Markup
from google.appengine.ext import db

ALLOWED_TAGS = (
        # bleach.ALLOWED_TAGS:
        'a', 'abbr', 'acronym', 'b',
        'blockquote', 'code', 'em', 'i',
        'li', 'ol', 'strong', 'ul',
        # more:
        'p', 'strike', 'img', 'table',
        'thead', 'tr', 'td', 'th',
        'hr', 'caption', 'summary',
        'tbody',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'div', 'big', 'small', 'tt', 'pre',
        )
ALLOWED_ATTRIBUTES = {
        # bleach.ALLOWED_ATTRIBUTES:
        'a': ['href', 'title'],
        'abbr': ['title'],
        'acronym': ['title'],
        # more:
        'img': ['src', 'alt', 'title'],
        'table': ['border', 'cellpadding', 'cellspacing', 'style',
            'bordercolor'],
        'th': ['scope'],
        'p': ['style'],
        'div': ['style'],
        }
ALLOWED_STYLES = (
        # (Bleach's default is no styles allowed)
        'color', 'width', 'height', 'background-color',
        'border-collapse', 'padding', 'border',
        'font-style',
        )

def bleach_entry(html):
    cleaned = bleach.clean(html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            styles=ALLOWED_STYLES,
            )
    return bleach.linkify(cleaned)

class BleachedTextAreaField(wtf.TextAreaField):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = bleach_entry(valuelist[0])
        else:
            self.data = ''

templates = {}
forms = {}
class ProfilePageForm(wtf.Form):
    # TODO BLEACHED
    text = wtf.TextAreaField('Introduction')
    curricular_aim = BleachedTextAreaField('Curricular Aim')

forms['profile'] = ProfilePageForm
templates['profile'] = 'wf_profile.html'

def viewable_model(model):
    # TODO maybe default values?
    d = db.to_dict(model)
    return { k: Markup(v) for k,v in d.items() }


