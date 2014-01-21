from google.appengine.ext import db
from common.prefetch import ensure_key
import datetime
import logging
from wiki_models import WikiPage, WikiComment, Annotation
from models.models import Student
from models import transforms
from modules.badges.badge_models import *
from webapp2 import cached_property
COUNT_LIMIT = 100

_parts = {
        1: {
            'assessments': ['Practices'],
            'assessments_required': False,
            'units': [1,2,3,4],
            'name': 'Assessment Practices',
            'slug': 'practices',
            'deadline': datetime.datetime(year=2013, month=10, day=20, hour=0, minute=0, second=0),
            },
        2: {
            'assessments': ['Principles'],
            'assessments_required': False,
            'units': [5,6,7],
            'name': 'Assessment Principles',
            'slug': 'principles',
            'deadline': datetime.datetime(year=2013, month=11, day=6, hour=0, minute=0, second=0),
            },
        3: {
            'assessments': ['Policies'],
            'assessments_required': False,
            'units': [8,9,10,11],
            'name': 'Assessment Policies',
            'slug': 'policies',
            'deadline': datetime.datetime(year=2013, month=12, day=4, hour=0, minute=0, second=0),
            },
        4: {
            'assessments': [],
            'assessments_required': False,
            'units': [12],
            'name': 'Assessment Expert',
            'slug': 'paper',
            'deadline': datetime.datetime(year=2014, month=1, day=4, hour=0, minute=0, second=0),
            },
        }


def get_part_num_by_badge_name(badge_name):
    badge_root = badge_name.split('.')[0]
    part = next((k for k,v in _parts.items() if v['slug'] == badge_root), None)
    if part is not None:
        return part
    raise KeyError('There is no part with the slug %s (%s)' % (badge_root, badge_name))

ASSESSMENT_PASSING_SCORE = 80

def find_badge_and_assertion(student, base_slug):
    # in order of preference for issuing
    slugs = (base_slug + '.leader', base_slug)
    badge_keys = [db.Key.from_path(Badge.kind(), s) for s in slugs]
    badge_ents = db.get(badge_keys)


    assertions = [Badge.is_issued_to(bk, student) for bk in badge_keys]

    # if they have actually received a badge, this will find it.
    for badge, assertion in zip(badge_ents, assertions):
        if assertion:
            if badge:
                return (badge, assertion)
            else:
                logging.warning('Found assertion %s for nonexistant badge :(',
                        assertion.key())

    # otherwise, we show the default badge.
    if not badge_ents[1]:
        logging.warning('No badges found with key_name %s (or .leader)', base_slug)

    return (badge_ents[1], None)


class PartReport(db.Model):
    part = db.IntegerProperty()
    slug = db.StringProperty()
    assessment_scores_json = db.TextProperty()
    student = db.ReferenceProperty(Student, indexed=True)
    timestamp = db.DateTimeProperty(indexed=False, auto_now_add=True)
    units_are_public = db.BooleanProperty(indexed=False, default=True)
    exam_display = db.StringProperty(indexed=False)
    review_is_public = db.BooleanProperty(indexed=False, default=True)

    @classmethod
    def on(cls, student, course, part, force_re_run=False, put=False):
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

        if force_re_run and report.is_saved():
            report._run(course)
        if put:
            report.put_all()
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

        (b, a) = find_badge_and_assertion(self.student, self.slug)
        self.badge = b
        self.badge_assertion = a

    def _run(self, course):
        config = _parts[self.part]
        self.slug = config['slug']
        self.timestamp = datetime.datetime.now()
        for ur in self.unit_reports:
            if ur.is_saved():
                ur._run()
        self._run_assessments(course)

    def _run_assessments(self, course):
        config = _parts[self.part]
        student_scores = course.get_all_scores(self.student)
        scores_to_save = []

        for exam_id in config['assessments']:
            for maybe_exam in student_scores:
                if maybe_exam['id'] != exam_id:
                    continue
                exam = maybe_exam
                exam['passing_score'] = ASSESSMENT_PASSING_SCORE
                exam['did_pass'] = exam['score'] >= ASSESSMENT_PASSING_SCORE
                scores_to_save.append(exam)

        self.assessment_scores_json = transforms.dumps(scores_to_save)

    @property
    def assessment_scores(self):
        return transforms.loads(self.assessment_scores_json)

    @cached_property
    def student_email(self):
        return type(self).student.get_value_for_datastore(self).name()

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
        assessments_required = self._config['assessments_required']
        return units_done and (assessments_done or not assessments_required)

    @property
    def incomplete_reasons(self):
        units = [ (u.unit, u.is_complete) for u in self.unit_reports ]
        tests = [ e['did_pass'] for e in self.assessment_scores ]
        assessments_required = self._config['assessments_required']
        inc_reasons = []

        for num, done in units:
            if not done:
                inc_reasons.append('Unit %d' % num)
        if not all(tests) and assessments_required:
            inc_reasons.append('Test')

        return inc_reasons

class UnitReport(db.Model):
    student = db.ReferenceProperty(Student, indexed=True)
    unit = db.IntegerProperty(indexed=True)
    timestamp = db.DateTimeProperty(indexed=False, auto_now_add=True)

    comments = db.IntegerProperty(indexed=False)
    endorsements = db.IntegerProperty(indexed=False)
    promotions = db.IntegerProperty(indexed=False)
    submitted = db.BooleanProperty(indexed=False)
    incomplete_reasons = db.StringListProperty(indexed=False)

    promotion_texts = db.StringListProperty(indexed=False)

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
        elif not self.promotion_texts:
            self._set_promotion_texts()

    def _run(self):
        page = self._page
        self.submitted = bool(page)
        if not page:
            self.comments = 0
            self.endorsements = 0
            self.promotions = 0
            self.incomplete_reasons = []
            return
        self.comments = page.comments.count(limit=COUNT_LIMIT)
        self.endorsements = Annotation.endorsements(page).count(limit=COUNT_LIMIT)
        self._set_promotion_texts()
        self.promotions = len(self.promotion_texts)
        self.incomplete_reasons = [inc.reason for inc in Annotation.incompletes(page).run(limit=10)]
        self.timestamp = datetime.datetime.now()

    def _set_promotion_texts(self):
        promos = Annotation.exemplaries(self._page).run(limit=COUNT_LIMIT)
        self.promotion_texts = [p.reason for p in promos]

    @cached_property
    def _page(self):
        return WikiPage.get_page(self.student, self.unit)

    @cached_property
    def wiki_fields(self):
        page = self._page
        return {k: getattr(page, k) for k in page.dynamic_properties()}

    @property
    def is_complete(self):
        return all((
                self.submitted,
                self.endorsements > 0,
                not self.incomplete_reasons,
                ))

FINAL_EXAM_PASSING_SCORE = 70
class ExpertBadgeReport(db.Model):
    # identifying this report
    student = db.ReferenceProperty(Student, indexed=True)
    timestamp = db.DateTimeProperty(auto_now_add=True)
    slug = 'expert'

    # display properties
    exam_display = db.StringProperty(indexed=False)
    link_to_other_badges = db.BooleanProperty(default=True, indexed=False)

    # conditions for getting the badge
    final_exam_score_json = db.TextProperty()
    done_with_survey = db.BooleanProperty(indexed=False)
    earned_practices = db.BooleanProperty(indexed=False)
    earned_principles = db.BooleanProperty(indexed=False)
    earned_policies = db.BooleanProperty(indexed=False)

    # shown in leader badge page
    exemplary_count = db.IntegerProperty(indexed=False)

    @classmethod
    def on(cls, student, course, force_re_run=False, put=False):
        q = cls.all()
        q.filter('student', student)
        reports = q.fetch(limit=2)
        if len(reports) > 1:
            raise AssertionError('Found more than one part report for part %d student %s' % (
                part, student.key().name()))
        elif len(reports) == 1:
            report = reports[0]
            if force_re_run:
                report._run(course)
        else:
            report = cls(None, student=student)
            report._run(course)

        if put:
            report.put()
        return report

    def __init__(self, *args, **kwargs):
        db.Model.__init__(self, *args, **kwargs)

        (b, a) = find_badge_and_assertion(self.student, 'expert')
        self.badge = b
        self.badge_assertion = a

    def _run(self, course):
        self._set_badge_flags()
        self._set_survey_flag()
        self._set_exam_info(course)
        self._set_exemplary_count()

    @cached_property
    def student_key(self):
        return type(self).student.get_value_for_datastore(self)

    def _set_badge_flags(self):
        assertions = BadgeAssertion.all().filter('recipient', self.student_key).run()
        for ass in assertions:
            slug_root = ass.badge_name.split('.')[0]
            if slug_root == 'practices':
                self.earned_practices = True
            elif slug_root == 'principles':
                self.earned_principles = True
            elif slug_root == 'policies':
                self.earned_policies = True

    def _set_survey_flag(self):
        # Here not at top to break import loop
        from modules.regconf.regconf import FormSubmission
        form_submissions = FormSubmission.all()
        form_submissions.filter('form_name', 'exit_survey_3')
        form_submissions.filter('user', self.student_key)
        self.done_with_survey = bool(form_submissions.count(limit=1))

    def _set_exam_info(self, course):
        looking_for = 'Final'
        self.final_exam_score_json = "{}"

        for exam in course.get_all_scores(self.student):
            if exam['id'] != looking_for:
                continue
            exam['passing_score'] = FINAL_EXAM_PASSING_SCORE
            exam['did_pass'] = exam['score'] >= FINAL_EXAM_PASSING_SCORE
            self.final_exam_score_json = transforms.dumps(exam)
            break

    def _set_exemplary_count(self):
        self.exemplary_count = Annotation.exemplaries(whose=self.student_key).count(limit=500)

    @property
    def final_exam_score(self):
        return transforms.loads(self.final_exam_score_json)

    @property
    def is_complete(self):
        return all((
                self.earned_practices,
                self.earned_principles,
                self.earned_policies,
                self.done_with_survey,
                self.final_exam_score['did_pass'],
                ))

    def incomplete_reasons(self):
        r = []
        if not self.earned_practices:
            r.append('Practices')
        if not self.earned_principles:
            r.append('Principles')
        if not self.earned_policies:
            r.append('Policies')
        if not self.done_with_survey:
            r.append('Survey')
        if not self.final_exam_score['did_pass']:
            r.append('Final')
        return r

    @cached_property
    def student_email(self):
        return type(self).student.get_value_for_datastore(self).name()

