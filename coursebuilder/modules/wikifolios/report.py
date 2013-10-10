from google.appengine.ext import db
from common.prefetch import ensure_key
import logging
from wiki_models import *
COUNT_LIMIT = 100

class UnitReport(object):
    # Maybe should be a handler?  Do I need course data?
    @classmethod
    def on(cls, student, unit):
        # Might change this to be a query rather than a creation
        return cls(student, unit)

    def __init__(self, student, unit):
        self.student = student
        self.unit = unit
        self._run()

    def _run(self):
        page = WikiPage.get_page(self.student, self.unit)
        self.submitted = bool(page)
        if not page:
            self.comments = 0
            self.endorsements = 0
            self.promotions = 0
            self.incomplete_reasons = []
            return
        self.comments = page.comments.count(limit=COUNT_LIMIT)
        self.endorsements = Annotation.endorsements(page).count(limit=COUNT_LIMIT)
        self.promotions = Annotation.exemplaries(page).count(limit=COUNT_LIMIT)
        self.incomplete_reasons = [inc.reason for inc in Annotation.incompletes(page).run(limit=10)]


    def is_complete(self):
        return all((
                self.submitted,
                self.endorsements > 0,
                not self.incomplete_reasons,
                ))

