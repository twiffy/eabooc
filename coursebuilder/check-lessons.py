#!/usr/bin/env python

import sys

import bleach
from bleach import callbacks
import sys
import shutil

for path in sys.argv[1:]:
    cooked = ''
    with open(path, 'r') as f:
        raw = f.read()
        # TODO also check links for being to google docs/drive
        cooked = bleach.linkify(raw,
                [callbacks.nofollow, callbacks.target_blank])
    with open(path, 'w') as f:
        f.truncate()
        f.encoding = 'utf8'
        f.write(cooked)


