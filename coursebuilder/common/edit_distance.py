"""
An optimized dynamic programming algorithm for calculating the Levenshtein
"editing" distance between two strings.  Used to see how much people's
Curricular Aims have been changed between units.
"""

import numpy as np
from unittest import TestCase

def levenshtein(source, target):
    if len(source) < len(target):
        return levenshtein(target, source)

    # So now we have len(source) >= len(target).
    if len(target) == 0:
        return len(source)

    # We call tuple() to force strings to be used as sequences
    source = np.array(tuple(source))
    target = np.array(tuple(target))

    # We use a dynamic programming algorithm, but with the
    # added optimization that we only need the last two rows
    # of the matrix.
    previous_row = np.arange(target.size + 1)
    for s in source:
        # Insertion (target grows longer than source):
        current_row = previous_row + 1

        # Substitution or matching:
        # Target and source items are aligned, and either
        # are different (cost of 1), or are the same (cost of 0).
        current_row[1:] = np.minimum(
                current_row[1:],
                np.add(previous_row[:-1], target != s))

        # Deletion (target grows shorter than source):
        current_row[1:] = np.minimum(
                current_row[1:],
                current_row[0:-1] + 1)

        previous_row = current_row

    return previous_row[-1]

class LevenshteinTest(TestCase):
    def test_bounds(self):
        self.assertEqual(levenshtein('', ''), 0)
        self.assertEqual(levenshtein('', 'asdf'), 4)
        self.assertEqual(levenshtein('asdf', ''), 4)
        self.assertEqual(levenshtein('asdf', 'asdf'), 0)
        self.assertEqual(levenshtein('jkl;', 'asdf'), 4)

    def test_word_lists(self):
        source = ('quick', 'brown', 'fox')
        t1 = source
        t2 = source + ('jumps',)
        self.assertEqual(levenshtein(source, t1), 0)
        self.assertEqual(levenshtein(source, t2), 1)

    def test_ins_del_subst(self):
        source = 'abcde'
        self.assertEqual(levenshtein(source, 'abzde'), 1)
        self.assertEqual(levenshtein(source, 'abde'), 1)
        self.assertEqual(levenshtein(source, 'abccde'), 1)
        self.assertEqual(levenshtein(source, 'zbzde'), 2)
        self.assertEqual(levenshtein(source, 'bzde'), 2)
        self.assertEqual(levenshtein(source, 'aabzde'), 2)
        self.assertEqual(levenshtein(source, 'azde'), 2)
        self.assertEqual(levenshtein(source, 'zzde'), 3)
        self.assertEqual(levenshtein(source, 'de'), 3)
        self.assertEqual(levenshtein(source, 'ae'), 3)
        self.assertEqual(levenshtein(source, 'ecde'), 2)
        self.assertEqual(levenshtein(source, 'azbcd'), 2)

    def test_deletions(self):
        source = 'abcdefghihgfedcba'
        for i in range(1, len(source)):
            dest = source[:-i]
            # deletions
            self.assertEqual(levenshtein(source, dest), i)
            self.assertEqual(levenshtein(source, source[:i-1] + source[i:]), 1)
