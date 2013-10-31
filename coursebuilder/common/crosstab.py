from itertools import combinations, chain
from collections import Counter, defaultdict

class CrossTab(object):
    def __init__(self):
        self._counter = Counter()
        self._seen_values = defaultdict(set)

    def add(self, **kwargs):
        # TODO: maybe notice any kwargs not expressed, and set them to None or Any or something.
        self._counter.update(chain.from_iterable(
                combinations(kwargs.items(), r) for r in xrange(len(kwargs) + 1)))
        for k, v in kwargs.iteritems():
            self._seen_values[k].add(v)

    def count(self, **kwargs):
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

    def test_asdf(self):
        ct = CrossTab()
        ct.add(cats='milk', dogs='walk')
        ct.add(cats='milk', dogs='run')
        ct.add(cats='milk', dogs='walk')
        ct.add(cats='milk', dogs='walk')
        ct.add(cats='milk', dogs='walk')
        ct.add(cats='cuddle', dogs='walk')
        print '\n'.join((str(row) for row in ct.table('cats', 'dogs')))

