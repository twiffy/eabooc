from google.appengine.ext import db
from common.prefetch import ensure_key
import datetime
import logging
from wiki_models import *
from modules.badges.badge_models import *
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


_parts = {
        1: {
            'assessments': 'Practices',
            'units': [1,2,3,4],
            'name': 'Assessment Practices',
            'slug': 'practices',
            'deadline': datetime.datetime(year=2013, month=10, day=20, hour=0, minute=0, second=0),
            },
        }

ASSESSMENT_PASSING_SCORE = 80

class PartReport(object):
    @classmethod
    def on(cls, student, course, part):
        return cls(student, course, part)

    def __init__(self, student, course, part):
        for k,v in _parts[part].iteritems():
            setattr(self, k, v)
        self.unit_reports = [UnitReport.on(student, u) for u in self.units]
        self.assessment_scores = []
        score_list = course.get_all_scores(student)
        for exam in score_list:
            if exam['id'] in self.assessments:
                exam['passing_score'] = ASSESSMENT_PASSING_SCORE
                exam['did_pass'] = exam['score'] >= ASSESSMENT_PASSING_SCORE
                self.assessment_scores.append(exam)

        # Find badge stuff!
        self.badge = Badge.get_by_key_name(self.slug)
        if self.badge:
            self.badge_assertion = Badge.is_issued_to(self.badge, student) # may be None
