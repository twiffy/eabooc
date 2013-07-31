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
