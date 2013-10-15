from google.appengine.ext import db
from common.prefetch import ensure_key
import datetime
import logging
from wiki_models import WikiPage, WikiComment, Annotation
from models.models import Student
from models import transforms
from modules.badges.badge_models import *
COUNT_LIMIT = 100

class UnitReport(db.Model):
    student = db.ReferenceProperty(Student, indexed=True)
    unit = db.IntegerProperty(indexed=True)
    timestamp = db.DateTimeProperty(indexed=False, auto_now_add=True)

    comments = db.IntegerProperty(indexed=False)
    endorsements = db.IntegerProperty(indexed=False)
    promotions = db.IntegerProperty(indexed=False)
    submitted = db.BooleanProperty(indexed=False)

    # JSON encoded..
    wiki_fields = db.TextProperty()

    @classmethod
    def on(cls, student, unit):
        q = cls.all()
        q.filter('student', student)
        q.filter('unit', unit)
        report = q.get()
        if not report:
            report = cls(student=student, unit=unit)
        return report

    def __init__(self, *args, **kwargs):
        super(UnitReport, self).__init__(*args, **kwargs)
        if not self.is_saved():
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
        self.wiki_fields = transforms.dumps({k: getattr(page, k) for k in page.dynamic_properties()})

    @property
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
            # Maybe this loop should be over self.assessments, so we make sure they show up
            # even if they are not submitted.
            if exam['id'] in self.assessments:
                exam['passing_score'] = ASSESSMENT_PASSING_SCORE
                exam['did_pass'] = exam['score'] >= ASSESSMENT_PASSING_SCORE
                self.assessment_scores.append(exam)

        # Find badge stuff!
        self.badge = Badge.get_by_key_name(self.slug)
        if self.badge:
            self.badge_assertion = Badge.is_issued_to(self.badge, student) # may be None

    @property
    def is_complete(self):
        units_done = all((
            u.is_complete for u in self.unit_reports))
        assessments_done = all((
            e['did_pass'] for e in self.assessment_scores))
        return units_done and assessments_done
