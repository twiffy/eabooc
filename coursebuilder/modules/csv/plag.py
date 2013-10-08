#!/usr/bin/env python

import re
from collections import defaultdict, Counter
import unicodecsv as csv
import sys


def k_window(coll, k):
    """
    >>> list(k_window('abcde', 4))
    ['abcd', 'bcde']
    >>> list(k_window('abcde', 5))
    ['abcde']
    >>> list(k_window('abcde', 6))
    []
    """
    max = len(coll)
    curr = 0
    while curr + k <= max:
        yield coll[curr:curr+k]
        curr += 1

def find_matches(records, id_col, k, exclude=[]):
    found = defaultdict(set)
    confidences = Counter()
    for rec in records:
        rec_id = rec[id_col]
        for col in rec.viewkeys() - set((id_col,)):
            rec_col_id = '%s:%s' % (rec_id, col)
            val = rec[col]
            if not val or col in exclude:
                continue
            val = val.lower()
            words = tuple(re.split(r'\W+', val))
            for window in k_window(words, k):
                h = hash(window)
                found[h].add(rec_col_id)
                other_sources = set(found[h])
                other_sources.discard(rec_col_id)
                confidences.update(
                        [tuple(sorted((rec_col_id, other))) for other in other_sources])
    #print 'Found', len(found), k, 'grams'
    #print 'Memory footprint is', sys.getsizeof(found), '(found), and', sys.getsizeof(confidences), '(confidences)'
    return confidences


