"""
Lots of stuff for sanitizing input text, removing XSS vulnerabilities and stuff.

There might be holes in this, but I think the worst they can do is make
the page look wonky - not that bad.

There are some tricks related to CKEditor - it *really* wants to be able to
make <p> tags, for instance.  So make sure things look alright after you make
any changes.  Check the git log for this file to see me messing with it.

Some tags are allowed in wikifolio posts, a smaller set are allowed in
comments.

Also monkey-patches wtforms, lulz.  This adds a "title" attribute to all
form input elements, to help out with accessibility.
"""
import wtforms as wtf
import bleach
from markupsafe import Markup

ALLOWED_TAGS = (
        # bleach.ALLOWED_TAGS has default:
        'a', 'abbr', 'acronym', 'b',
        'blockquote', 'code', 'em', 'i',
        'li', 'ol', 'strong', 'ul',
        # my additions:
        'p', 'strike', 'img', 'table',
        'thead', 'tr', 'td', 'th',
        'hr', 'caption', 'summary',
        'tbody',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'div', 'big', 'small', 'tt', 'pre',
        )
ALLOWED_ATTRIBUTES = {
        # default bleach.ALLOWED_ATTRIBUTES:
        'a': ['href', 'title'],
        'abbr': ['title'],
        'acronym': ['title'],
        # my additions:
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
            strip=True,
            )
    return bleach.linkify(cleaned)

COMMENT_TAGS = (
        'a', 'b',
        'blockquote', 'i',
        'li', 'ol', 'ul',
        'p', 'tt',
        )
COMMENT_ATTRIBUTES = {
        # bleach.ALLOWED_ATTRIBUTES:
        'a': ['href', 'title'],
        }
COMMENT_STYLES = ()

def bleach_comment(html):
    return bleach.clean(html,
            tags=COMMENT_TAGS,
            attributes=COMMENT_ATTRIBUTES,
            styles=COMMENT_STYLES,
            strip=True,
            )


# Monkey patch wtforms.Field so that each field gets a Title attribute
def _awesome_field_call(field_self, **kwargs):
    args = {'title': Markup(field_self.label.text).striptags()}
    args.update(kwargs)
    return field_self.widget(field_self, **args)

wtf.Field.__call__ = _awesome_field_call

class BleachedTextAreaField(wtf.TextAreaField):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = bleach_entry(valuelist[0])
        else:
            self.data = ''

    def read_only_view(self):
        return self.data or ''
