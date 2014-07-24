#!/usr/bin/env python
"""
Plagiarism detection!

This is a pretty well-explored area of computer science, I just googled around
until I found a reasonable way to do it
(http://en.wikipedia.org/wiki/Rabin%E2%80%93Karp_algorithm - published in
1987).  Luckily, that way worked fine for a course of our size.  Basically, it
looks at all the student submissions, and notices if they have any long
stretches of text (10 words) in common.  The 'similarity score' between two
documents is the count of how many (possibly overlapping) 10-word passages they
have in common.  To simplify, it's approximately the number of words they have
in common in a row.  The algorithm would scale fine to an enormous course, but
it would run many times more slowly - maybe we could only run it once a day or
something.  That would be fine, I imagine, but would involve some rewriting of
the code.

This approach is very good at detecting straight up copy pasting.  But, if
someone changes one word per sentence or so, this approach will not work at
all.  There are more advanced versions out there, that might still detect it.
There are actually quite a number of online services that do some version of
plagiarism detection: http://turnitin.com/
https://www.writecheck.com/static/home.html
http://www.dustball.com/cs/plagiarism.checker/
http://www.plagscan.com/seesources/ (and many more).

I guess how I would position this work is that it's necessary to have some sort
of check, in a course where students see each other's work.  But at this point,
we're not pushing back the state of the art or anything.  I did it in two
hours, some folks have spent years on it (for instance, see the 2nd
International Competition on Plagiarism Detection:
http://repository.dlsi.ua.es/497/1/PotthastEtAl_PAN_CLEF10.pdf).
"""

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


