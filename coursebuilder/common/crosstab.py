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

    def add_count(self, count, **kwargs):
        for combo in self._all_key_combos(kwargs.items()):
            self._counter[combo] += count
        for k, v in kwargs.iteritems():
            self._seen_values[k].add(v)

    def _all_key_combos(self, keys):
        for r in xrange(len(keys) + 1):
            for combo in combinations(keys, r):
                yield tuple(sorted(combo))

    def count(self, **kwargs):
        key = tuple(sorted(kwargs.items()))
        return self._counter[tuple(sorted(kwargs.items()))]

    def values(self, attr):
        return self._seen_values[attr]

    def table(self, row, col=None):
        col_values = sorted(self.values(col))
        row_values = sorted(self.values(row))
        yield ('',) + tuple(':'.join((col, str(c))) for c in col_values) + ('Total',)
        for r in row_values:
            label = ':'.join((row, str(r)))
            yield (label,) + tuple(
                    self.count(**{
                        col: c,
                        row: r}) for c in col_values
                    ) + (self.count(**{row: r}),)
        if col:
            yield ('Total',) + tuple(
                    self.count(**{col: c}) for c in col_values) + ('',)

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

    def test_add_count(self):
        ct = CrossTab()
        ct.add(cats='milk', dogs='woof')
        ct.add_count(5, cats='purr', dogs='woof')
        self.assertEqual(ct.count(), 6)
        self.assertEqual(ct.count(dogs='woof'), 6)
        self.assertEqual(ct.count(cats='woof'), 0)
        self.assertEqual(ct.count(cats='milk'), 1)
        self.assertEqual(ct.count(cats='purr'), 5)

    def test_table_totals(self):
        ct = CrossTab()
        ct.add(cats=1, dogs=2, lemurs=1)
        ct.add(cats=1, dogs=2, lemurs=2)
        ct.add(cats=2, dogs=1, lemurs=3)
        ct.add(cats=2, dogs=1, lemurs=4)
        ct.add(cats=2, dogs=1, lemurs=5)
        tab = list(ct.table('cats', None))
        self.assertEqual(len(tab), 3)
        self.assertEqual(tab[1][1], 2)
        self.assertEqual(tab[2][1], 3)

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

    def test_none(self):
        ct = CrossTab()
        ct.add(foo='a', bar=None)
        list(ct.table('foo', 'bar'))
        list(ct.table('bar', 'foo'))
