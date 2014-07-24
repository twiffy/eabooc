"""
ckeditor.py - translate from Bleach's allowed content to CKEditor's.

Both Bleach (python library for sanitizing user input) and CKEditor (WYSIWYG
editor in HTML + JS) have ways to specify what tags, styles, etc. are allowed.
This function translates from Bleach's format to CKEditor's format, so that the
editor doesn't let the users do something that Bleach then discards.
"""
import StringIO

def allowed_content(tags, attributes={}, styles=()):
    """
    >>> allowed_content(['a', 'h1'])
    'a;h1;'
    >>> allowed_content(['a', 'h1'], {'a': ('href',)})
    'a[href];h1;'
    >>> allowed_content(['a', 'h1'], styles=('color', 'background-color'))
    'a{color,background-color};h1{color,background-color};'
    """
    allowed = StringIO.StringIO()

    for tag in tags:
        allowed.write(tag)
        if tag in attributes:
            allowed.write('[')
            allowed.write(",".join(attributes[tag]))
            allowed.write(']')
        if styles:
            allowed.write('{')
            allowed.write(",".join(styles))
            allowed.write('}')

        allowed.write(';')

    return allowed.getvalue()



if __name__ == "__main__":
    import doctest
    doctest.testmod()
