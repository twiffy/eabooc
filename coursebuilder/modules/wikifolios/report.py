from google.appengine.ext import db
from common.prefetch import ensure_key
import datetime
import logging
from wiki_models import WikiPage, WikiComment, Annotation
from models.models import Student
from models import transforms
from modules.badges.badge_models import *
COUNT_LIMIT = 100

_parts = {
        1: {
            'assessments': ['Practices'],
            'units': [1,2,3,4],
            'name': 'Assessment Practices',
            'slug': 'practices',
            'deadline': datetime.datetime(year=2013, month=10, day=20, hour=0, minute=0, second=0),
            },
        }

ASSESSMENT_PASSING_SCORE = 80


class PartReport(db.Model):
    part = db.IntegerProperty()
    slug = db.StringProperty()
    assessment_scores_json = db.TextProperty()
    student = db.ReferenceProperty(Student, indexed=True)
    timestamp = db.DateTimeProperty(indexed=False, auto_now_add=True)

    @classmethod
    def on(cls, student, course, part):
        q = cls.all()
        q.filter('student', student)
        q.filter('part', part)
        reports = q.fetch(limit=2)
        if len(reports) > 1:
            raise AssertionError('Found more than one part report for part %d student %s' % (
                part, student.key().name()))
        elif len(reports) == 1:
            report = reports[0]
        else:
            report = cls(None, course=course, student=student, part=part)
        return report

    def __init__(self, *args, **kwargs):
        course = None
        if 'course' in kwargs:
            course = kwargs['course']
            del kwargs['course']
        super(PartReport, self).__init__(*args, **kwargs)

        self._config = _parts[self.part]

        if not self.is_saved():
            self._run(course)

    def _run(self, course):
        config = _parts[self.part]
        self.slug = config['slug']
        student_scores = course.get_all_scores(self.student)
        scores_to_save = []

        for exam_id in config['assessments']:
            for maybe_exam in student_scores:
                print 'Considering %s for %s' % (maybe_exam['id'], exam_id)
                if maybe_exam['id'] != exam_id:
                    continue
                exam = maybe_exam
                exam['passing_score'] = ASSESSMENT_PASSING_SCORE
                exam['did_pass'] = exam['score'] >= ASSESSMENT_PASSING_SCORE
                scores_to_save.append(exam)

        self.assessment_scores_json = transforms.dumps(scores_to_save)

    @cached_property
    def badge(self):
        return Badge.get_by_key_name(self.slug)

    @cached_property
    def badge_assertion(self):
        if self.badge:
            return Badge.is_issued_to(self.badge, self.student) # may be None

    @property
    def assessment_scores(self):
        return transforms.loads(self.assessment_scores_json)

    @cached_property
    def unit_reports(self):
        return [UnitReport.on(self.student, u) for u in self._config['units']]

    def put_all(self):
        for rep in self.unit_reports:
            rep.put()
        self.put()

    def get_unit(self, num):
        reports = self.unit_reports
        for r in reports:
            if r.unit == num:
                return r
        return None

    @property
    def is_complete(self):
        units_done = all((
            u.is_complete for u in self.unit_reports))
        assessments_done = all((
            e['did_pass'] for e in self.assessment_scores))
        return units_done and assessments_done


class UnitReport(db.Model):
    student = db.ReferenceProperty(Student, indexed=True)
    unit = db.IntegerProperty(indexed=True)
    timestamp = db.DateTimeProperty(indexed=False, auto_now_add=True)

    comments = db.IntegerProperty(indexed=False)
    endorsements = db.IntegerProperty(indexed=False)
    promotions = db.IntegerProperty(indexed=False)
    submitted = db.BooleanProperty(indexed=False)
    incomplete_reasons = db.StringListProperty(indexed=False)

    # JSON encoded..
    wiki_fields = db.TextProperty()

    @classmethod
    def on(cls, student, unit):
        q = cls.all()
        q.filter('student', student)
        q.filter('unit', unit)
        reports = q.fetch(limit=2)
        if len(reports) > 1:
            raise AssertionError('Found more than one unit report for unit %d student %s' % (
                unit, student.key().name()))
        elif len(reports) == 1:
            report = reports[0]
        else:
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
