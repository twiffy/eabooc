from itertools import combinations, chain
from collections import Counter, defaultdict

class CrossTab(object):
    def __init__(self):
        self._counter = Counter()
        self._seen_values = defaultdict(set)

    def add(self, **kwargs):
        # TODO: maybe notice any kwargs not expressed, and set them to None or Any or something.
        self._counter.update(self._all_key_combos(kwargs.items()))
        for k, v in kwargs.iteritems():
            self._seen_values[k].add(v)

    def _all_key_combos(self, keys):
        for r in xrange(len(keys) + 1):
            for combo in combinations(keys, r):
                yield tuple(sorted(combo))

    def count(self, **kwargs):
        key = tuple(sorted(kwargs.items()))
        print 'Looking for %s' % repr(key)
        return self._counter[tuple(sorted(kwargs.items()))]

    def values(self, attr):
        return self._seen_values[attr]

    def table(self, row, col):
        col_values = sorted(self.values(col))
        row_values = sorted(self.values(row))
        yield ('',) + tuple(':'.join((col, c)) for c in col_values)
        for r in row_values:
            yield (':'.join((row, str(r))),) + tuple(
                    self.count(**{
                        col: c,
                        row: r}) for c in col_values)

import unittest
def rotate(lst):
    return lst[1:] + [lst[0]]

class CrossTabTest(unittest.TestCase):
    def test_single(self):
        ct = CrossTab()
        ct.add(foo='bar')
        self.assertEqual(ct.count(foo='bar'), 1)

    def test_double(self):
        ct = CrossTab()
        ct.add(cats='milk', dogs='walk')
        ct.add(dogs='walk', bunnies='hold')
        self.assertEqual(ct.count(), 2)
        self.assertEqual(ct.count(dogs='walk'), 2)
        self.assertEqual(ct.count(bunnies='hold'), 1)
        self.assertEqual(ct.count(cats='milk'), 1)

    def test_sorta_query(self):
        ct = CrossTab()
        ct.add(cats='milk', dogs='walk')
        ct.add(dogs='walk', bunnies='hold')
        self.assertEqual(ct.values('dogs'), set(('walk',)))

    def test_sums(self):
        animals = ['cat', 'dog', 'bunny']
        who = ['jane', 'kate', 'montmorency', 'elwood']
        ct = CrossTab()
        for w in who:
            animals = rotate(animals)
            rankings = dict(zip(animals, range(len(animals))))
            rankings['who'] = w
            ct.add(**rankings)
        for animal in animals:
            # Assert that each person's vote is reflected in the counts
            self.assertEqual(len(who), sum(
                ct.count(**{animal: r}) for r in range(len(animals))))

            # Assert that the sum of all the rankings for one animal
            # is equal to the number of voters
            self.assertEqual(len(who), sum(
                ct.count(**{animal: r, 'who': p})
                    for r in range(len(animals)) for p in who))

        #print '\n'.join(str(r) for r in ct._counter.iteritems())
        #print ct._seen_values
        #print '\n'.join((str(row) for row in ct.table('cat', 'who')))
        #print '\n'.join((str(row) for row in ct.table('dog', 'who')))
        #print '\n'.join((str(row) for row in ct.table('bunny', 'who')))
