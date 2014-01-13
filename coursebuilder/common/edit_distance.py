import numpy as np
from unittest import TestCase

def levenshtein(source, target):
    if len(source) < len(target):
        return levenshtein(target, source)

    # So now we have len(source) >= len(target).
    if len(target) == 0:
        return len(source)

    # We use a dynamic programming algorithm, but with the
    # added optimization that we only need the last two rows
    # of the matrix.
    previous_row = np.arange(len(target) + 1)
    current_row = previous_row + 1
    # s = source[i], t = target[j]
    for i, s in enumerate(source):
        current_row[0] = i + 1

        for j, t in enumerate(target):
            # find possible values for current_row[j+1]
            insert = previous_row[j + 1] + 1
            delete = current_row[j] + 1
            # subst has 0 cost if s == t
            subst = previous_row[j] + (s != t)

            current_row[j + 1] = min(insert, delete, subst)

        # Swap current and previous rows
        (previous_row, current_row) = (current_row, previous_row)

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

