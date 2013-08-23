#!/usr/bin/env python

import sys

import bleach
from bleach import callbacks
import sys
import shutil
from html5lib.tokenizer import HTMLTokenizer
import html5lib

# monkey patch html5lib so bleach.linkify treats documents as whole documents,
# not fragments
html5lib.HTMLParser.parseFragment = html5lib.HTMLParser.parse

current_file = None

def check_for_gdrive(attrs, new=False):
    if 'docs.google.com' in attrs['href']:
        print >>sys.stderr, "Warning: link to google docs in %s" % current_file
    return attrs

for path in sys.argv[1:]:
    cooked = ''
    current_file = path
    with open(path, 'r') as f:
        raw = f.read()
        # TODO also check links for being to google docs/drive
        cooked = bleach.linkify(raw, [
                    callbacks.nofollow,
                    callbacks.target_blank,
                    check_for_gdrive,
                    ],
                    tokenizer=HTMLTokenizer)
    with open(path, 'w') as f:
        f.truncate()
        f.write(cooked.encode('utf-8'))
