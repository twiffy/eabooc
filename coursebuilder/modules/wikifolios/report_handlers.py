from controllers.utils import BaseHandler, ReflectiveRequestHandler, XsrfTokenManager
from common import prefetch
import pprint
from models.roles import Roles
import re
from collections import defaultdict
from models import transforms
from modules.badges.badge_models import Badge, BadgeAssertion
from report import UnitReport, PartReport, ExpertBadgeReport
from report import _parts as part_config
from models.models import Student
from models.models import EventEntity
from wiki_models import Annotation
from jinja2 import Markup
import urllib
import wtforms as wtf
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import deferred
import page_templates
from common.querymapper import LoggingMapper
import logging

import wtforms as wtf

def exam_display_choices(exam_info):
    choices = [
            ('blank', '(Blank)'),
            ]
    default = 'blank'

    if exam_info['completed']:
        choices.append( ('completed', 'Submitted the exam') )

    if exam_info['did_pass']:
        choices.append( ('passed', 'Passed the exam, with at least (passing score) out of 100%') )
        choices.append( ('scored', 'Passed the exam, scoring (your score) out of 100%') )

        default = 'passed'

    return locals()


class EvidenceHandler(BaseHandler, ReflectiveRequestHandler):
    get_actions = ['view', 'settings']
    default_action = 'view'
    post_actions = ['save_settings']

    class SettingsForm(wtf.Form):
        report_id = wtf.HiddenField()
        units_are_public = wtf.BooleanField(
                "Show my Wikifolio entries for this badge on the evidence page?")

        # Will set choices dynamically.
        exam_display = wtf.SelectField(
                "How to display exam scores on the evidence page?")

        review_is_public = wtf.BooleanField(
                """Show the instructor's review of the paper on the evidence page?  Only
                relevant for the term paper.""")

    def get_settings(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return

        try:
            report = PartReport.get_by_id(int(self.request.GET.get('id', -1)))
        except ValueError:
            report = None
        if not report:
            self.abort(404, "That evidence report was not found.")

        if not self.can_edit(user, report):
            self.abort(403)

        form = self.SettingsForm(
                report_id=report.key().id(),
                units_are_public=report.units_are_public,
                exam_display=report.exam_display,
                review_is_public=report.review_is_public)


        #if report.part != 4:
            #del form.review_is_public

        display_field_params = {
                'choices': [('blank', '(Blank)')],
                'default': 'blank'
                }

        if report.assessment_scores:
            if len(report.assessment_scores) > 1:
                logging.warning("Evidence page settings assuming there's just one exam per part, but there is more than one")
            display_field_params = exam_display_choices(
                    report.assessment_scores[0])

        form.exam_display.choices = display_field_params['choices']
        form.exam_display.default = display_field_params['default']

        self.template_value['report'] = report
        self.template_value['form'] = form
        self.template_value['xsrf_token'] = XsrfTokenManager.create_xsrf_token('save_settings')
        self.template_value['navbar'] = {}
        self.template_value['action_url'] = '/badges/evidence?action=save_settings'
        self.template_value['badge_name'] = report._config['name']
        self.render('wf_evidence_settings.html')

    def can_edit(self, user, report):
        #Roles.is_course_admin(self.app_context)
        return report.student_email == user.key().name()

    def post_save_settings(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return

        form = self.SettingsForm(self.request.POST)

        try:
            report = PartReport.get_by_id(int(form.report_id.data))
        except ValueError:
            report = None
        if not report:
            self.abort(404, "That evidence report was not found.")

        if not self.can_edit(user, report):
            self.abort(403, "You can't edit that user's report.")

        if report.assessment_scores:
            display_field_params = exam_display_choices(
                    report.assessment_scores[0])
            form.exam_display.choices = display_field_params['choices']
            form.exam_display.default = display_field_params['default']
        else:
            del form.exam_display

        if not form.validate():
            self.redirect('/')
            return

        report.units_are_public = form.units_are_public.data
        report.review_is_public = form.review_is_public.data
        if report.assessment_scores:
            report.exam_display = form.exam_display.data
        report.put()

        EventEntity.record(
                'set-evidence-settings',
                users.get_current_user(),
                transforms.dumps({
                    'part': report.part,
                    'slug': report.slug,
                    'review_is_public': report.review_is_public,
                    'public': report.units_are_public,
                    'exam_display': report.exam_display,
                    'email': user.key().name()
                    }))

        self.template_value['navbar'] = {}
        self.template_value['content'] = '''<div class="gcb-aside">OK, saved settings.<br>
        <a href="/student/home">Back to your account page...</a></div>'''
        self.render('bare.html')

    def head(self):
        try:
            report = PartReport.get_by_id(int(self.request.GET.get('id', -1)))
        except ValueError:
            report = None
        if not report:
            self.abort(404)

        self.abort(200)

    def get_view(self):
        try:
            report = PartReport.get_by_id(int(self.request.GET.get('id', -1)))
        except ValueError:
            report = None
        if not report:
            self.abort(404)

        if not report.exam_display:
            if report.assessment_scores:
                display_info = exam_display_choices(report.assessment_scores[0])
                report.exam_display = display_info['default']
            else:
                report.exam_display = 'blank'

        self.report = report
        self.template_value['inline_save'] = lambda: ''
        self.template_value['navbar'] = {}
        self.template_value['author'] = self.report.student
        self.template_value['review_is_public'] = self.report.review_is_public
        if report.units_are_public:
            self.template_value['unit_link'] = self._unit_link
        else:
            self.template_value['unit_link'] = None
            self.template_value['no_unit_links'] = True
        self.template_value['unit_title'] = self._unit_title

        self.unit_num = None
        try:
            if report.units_are_public:
                self.unit_num = int(self.request.GET.get('unit', ''))
        except ValueError:
            self.unit_num = None

        if self.unit_num:
            self.unit = self.report.get_unit(self.unit_num)
            if self.unit:
                self.render_unit()
                return
            else:
                logging.warning('Could not find the right unit %d for PartReport %s',
                        self.unit_num, self.report.key())
        self.render_top()

    def _unit_link(self, unit):
        return self.request.path + "?" + urllib.urlencode({
            'id': self.request.GET['id'],
            'unit': unit,
            })

    def _unit_title(self, unit):
        unit_obj = self.find_unit_by_id(unit)
        title = unit_obj.title
        title = re.sub(r'\(.*?\)', '', title)
        return title.strip()

    def render_unit(self):
        fields = {
                k: Markup(v) for k,v in self.unit.wiki_fields.iteritems()}
        fields['reflection'] = Markup('<p><i>Removed from this view for peers\' privacy.<br>--BOOC Instructors and Tech Staff</i></p>')
        self.template_value['fields'] = fields
        self.template_value['unit'] = self.find_unit_by_id(self.unit_num)
        self.template_value['report'] = self.unit
        self.template_value['badge_slug'] = self.report.badge.key().name()
        self.template_value['layout_template'] = 'wf_evidence.html'
        self.template_value['review'] = Annotation.reviews(whose=self.report.student, unit=self.unit_num).get()
        self.render(page_templates.templates[self.unit_num])

    def render_top(self):
        self.template_value['part'] = self.report
        self.render('wf_evidence_top.html')

class ExpertEvidenceHandler(BaseHandler, ReflectiveRequestHandler):
    get_actions = ['view', 'settings']
    default_action = 'view'
    post_actions = ['save_settings']

    def can_edit(self, user, report):
        return report.student_email == user.key().name()

    class SettingsForm(wtf.Form):
        report_id = wtf.HiddenField()

        # Will set choices dynamically.
        exam_display = wtf.SelectField(
                "How to display exam scores on the evidence page?")

    def get_settings(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return

        try:
            report = ExpertBadgeReport.get_by_id(int(self.request.GET.get('id', -1)))
        except ValueError:
            report = None
        if not report:
            self.abort(404, "That evidence report was not found.")

        if not self.can_edit(user, report):
            self.abort(403)

        form = self.SettingsForm(
                report_id=report.key().id(),
                exam_display=report.exam_display)

        display_field_params = {
                'choices': [('blank', '(Blank)')],
                'default': 'blank'
                }

        display_field_params = exam_display_choices(
                report.final_exam_score)

        form.exam_display.choices = display_field_params['choices']
        form.exam_display.default = display_field_params['default']

        self.template_value['report'] = report
        self.template_value['form'] = form
        self.template_value['xsrf_token'] = XsrfTokenManager.create_xsrf_token('save_settings')
        self.template_value['navbar'] = {}
        self.template_value['badge_name'] = "Assessment Expert Badge"
        self.template_value['action_url'] = '/badges/expert_evidence?action=save_settings'
        self.render('wf_evidence_settings.html')

    def post_save_settings(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return

        form = self.SettingsForm(self.request.POST)

        try:
            report = ExpertBadgeReport.get_by_id(int(form.report_id.data))
        except ValueError:
            report = None
        if not report:
            self.abort(404, "That evidence report was not found.")

        if not self.can_edit(user, report):
            self.abort(403, "You can't edit that user's report.")

        display_field_params = exam_display_choices(
                report.final_exam_score)
        form.exam_display.choices = display_field_params['choices']
        form.exam_display.default = display_field_params['default']

        if not form.validate():
            self.redirect('/')
            return

        report.exam_display = form.exam_display.data
        report.put()

        EventEntity.record(
                'set-evidence-settings',
                users.get_current_user(),
                transforms.dumps({
                    'slug': report.slug,
                    'exam_display': report.exam_display,
                    'email': user.key().name()
                    }))

        self.template_value['navbar'] = {}
        self.template_value['content'] = '''<div class="gcb-aside">OK, saved settings.<br>
        <a href="/student/home">Back to your account page...</a></div>'''
        self.render('bare.html')

    def get_view(self):
        try:
            report = ExpertBadgeReport.get_by_id(int(self.request.GET.get('id', -1)))
        except ValueError:
            report = None
        if not report:
            self.abort(404)

        all_assertions_q = BadgeAssertion.all()
        all_assertions_q.filter('recipient', report.student_key)
        all_assertions_q.filter('revoked', False)
        all_assertions = all_assertions_q.run(limit=10)

        if not report.exam_display:
            if report.final_exam_score:
                display_info = exam_display_choices(report.final_exam_score)
                report.exam_display = display_info['default']
            else:
                report.exam_display = 'blank'

        self.template_value['report'] = report
        self.template_value['navbar'] = {}
        self.template_value['author'] = report.student
        # TODO: links to the other badges

        all_assertions = prefetch.prefetch_refprops(
                list(all_assertions), BadgeAssertion.badge)
        course_parts = {'practices': None, 'principles': None, 'policies': None}
        for ass in all_assertions:
            name_parts = ass.badge_name.split('.')
            if name_parts[0] in course_parts:
                if (not course_parts[name_parts[0]]) or (len(name_parts) > 1):
                    course_parts[name_parts[0]] = ass
        self.template_value['part_assertions'] = course_parts

        self.render('wf_expert_evidence.html')


class SingleIssueHandler(BaseHandler):
    class Form(wtf.Form):
        part = wtf.IntegerField('Which part of the course to issue a badge for? (1,2,3)')
        really_save = wtf.BooleanField('Really issue the badge and freeze the scores?', default=False)
        re_run = wtf.BooleanField('Re-run all unit and part reports? Will delete old ones if you also choose Really freeze above.', default=False)
        email = wtf.StringField('The email of the student to reconsider')

    def get(self):
        if not users.is_current_user_admin():
            self.abort(403)
        form = self.Form()
        self.template_value['form'] = form
        self.template_value['xsrf_token'] = XsrfTokenManager.create_xsrf_token('post')
        self.template_value['action_url'] = self.request.url
        self.template_value['title'] = 'Reconsider a single participant'
        self.render('badge_bulk_issue.html')

    def post(self):
        if not users.is_current_user_admin():
            self.abort(403)
        if not XsrfTokenManager.is_xsrf_token_valid(self.request.POST.get('xsrf_token', ''), 'post'):
            self.abort(403, 'XSRF token failed.')
        form = self.Form(self.request.POST)
        if not form.validate():
            self.response.write('<br>'.join(form.errors))
            return

        student = Student.get_by_key_name(form.email.data)
        report = PartReport.on(student, course=self.get_course(),
                part=form.part.data,
                force_re_run=form.re_run.data,
                put=form.really_save.data)

        badge = Badge.get_by_key_name(part_config[form.part.data]['slug'])
        if not badge:
            self.response.write(' There is no badge with key_name %s (so I cannot issue a badge)' % report.slug)

        if report.is_complete:
            if form.really_save.data and badge:
                b = Badge.issue(badge, student, put=False) # need to include evidence URL here somehow
                b.evidence = self.request.host_url + '/badges/evidence?id=%d' % report.key().id()
                b.put()
                self.response.write('Issued the badge!')
            else:
                self.response.write('Would have issued the badge!')
        else:
            self.response.write('Not issuing because: %s' % (', '.join(report.incomplete_reasons)))


class BulkIssueMapper(LoggingMapper):
    KIND = Student
    FILTERS = [('is_participant', True)]

    def __init__(self, really, course, part, host_url, re_run):
        super(BulkIssueMapper, self).__init__()
        self.really = really
        self.course = course
        self.part = part
        self.host_url = host_url
        self.re_run = re_run
        self.num_issued = 0

    def map(self, student):
        self.log.append('########## Student %s ##########' % student.key().name())
        report = PartReport.on(student, course=self.course, part=self.part,
                force_re_run=self.re_run, put=self.really)

        self.log.append(' Passed? %s.' % report.is_complete)

        badge = Badge.get_by_key_name(part_config[self.part]['slug'])
        if not badge:
            self.log.append(' There is no badge with key_name %s (so I cannot issue a badge)' % report.slug)

        if report.is_complete:
            self.num_issued += 1
            if self.really and badge:
                b = Badge.issue(badge, student, put=False) # need to include evidence URL here somehow
                b.evidence = self.host_url + '/badges/evidence?id=%d' % report.key().id()
                b.put()
                self.log.append(' Issued badge, name=%s, assertion id=%d' % (
                    badge.key().name(), b.key().id()))
                return ([b], [])
            else:
                self.log.append(' WOULD issue badge.')
        else:
            self.log.append('Not issuing because: %s' % (', '.join(report.incomplete_reasons)))

            if self.really and badge:
                Badge.ensure_not_issued(badge, student)
        return ([], [])

    def finish(self):
        self.log.append('DONE.  Issued %d badges total.' % self.num_issued)
        self._batch_write()


class BulkExpertBadgeIssueMapper(LoggingMapper):
    KIND = Student
    FILTERS = [('is_participant', True)]

    def __init__(self, really, course, unused_part_num, host_url, force_re_run):
        LoggingMapper.__init__(self)
        self.really = really
        self.course = course
        self.host_url = host_url
        self.force_re_run = force_re_run

        self.badge = Badge.get_by_key_name('expert')
        self.num_issued = 0

    def map(self, student):
        self.log.append('--------------- Student %s' % student.key().name())

        report = ExpertBadgeReport.on(student, self.course,
                force_re_run=self.force_re_run, put=self.really)

        self.log.append('Passed? %s.' % report.is_complete)

        if report.is_complete:
            self.num_issued += 1
            if self.really and self.badge:
                b = Badge.issue(self.badge, student, put=False) # need to include evidence URL here somehow
                b.evidence = self.host_url + '/badges/expert_evidence?id=%d' % report.key().id()
                b.put()
                self.log.append(' Issued badge, name=%s, assertion id=%d' % (
                    self.badge.key().name(), b.key().id()))
                return ([b], [])
            else:
                self.log.append(' WOULD issue badge.')
        else:
            self.log.append('Incomplete, we are missing: %s' % (', '.join(report.incomplete_reasons())))
        
        return ([], [])

    def finish(self):
        self.log.append('DONE.  Issued %d badges total.' % self.num_issued)
        self._batch_write()

NOBODY = object()
def default_dict_entry():
    return ([NOBODY], -1)

class BulkLeaderIssueMapper(LoggingMapper):
    KIND = Student
    FILTERS = [('is_participant', True)]

    def __init__(self, really, course, part, host_url, re_run):
        super(BulkLeaderIssueMapper, self).__init__()
        self.really = really
        self.course = course
        self.part = part
        self.host_url = host_url
        self.re_run = re_run
        self.best_by_group = defaultdict(default_dict_entry)
        self.leader_badge_key = part_config[part]['slug'] + '.leader'

        leader_badge = Badge.get_by_key_name(self.leader_badge_key)
        if not leader_badge:
            logging.warning('No badge with key_name: %s', self.leader_badge_key)
            self.log.append('No badge with key_name: %s'% self.leader_badge_key)
            if self.really:
                raise ValueError('No badge with key_name: %s' % self.leader_badge_key)

    def map(self, student):
        self.log.append('######### Student %s ##########' % student.key().name())

        part_report = PartReport.on(student, course=self.course, part=self.part,
                force_re_run=self.re_run)
        if not part_report.is_complete:
            self.log.append(' Skipping, since not complete.')
            return ([], [])

        self.log.append(' Part is complete, considering units.')

        unit_reports = part_report.unit_reports
        promotions = 0

        for ur in unit_reports:
            promotions += ur.promotions

        best_so_far = self.best_by_group[student.group_id][1]
        if promotions > best_so_far:
            self.best_by_group[student.group_id] = ([student.key().name()], promotions)

            self.log.append(' They have current best for group %s, with %d.' % (
                student.group_id, promotions))

        elif promotions == best_so_far:
            self.best_by_group[student.group_id][0].append(student.key().name())

            self.log.append(' They ARE TIED FOR CURRENT BEST for group %s, with %d.' % (
                student.group_id, promotions))
        return ([], [])

    def finish(self):
        if self.really:
            leader_badge = Badge.get_by_key_name(self.leader_badge_key)
        for group_id, (emails, count) in self.best_by_group.iteritems():
            self.log.append('Considering group %s, best score is %d' % (
                str(group_id), count))
            if count < 1:
                self.log.append('... Best score is too low, skipping.')
                continue
            if self.really:
                for email in emails:
                    b = Badge.issue(leader_badge,
                            db.Key.from_path(Student.kind(), email), put=False)
                    report = PartReport.on(
                            db.Key.from_path(Student.kind(), email),
                            course=self.course, part=self.part,
                            force_re_run=self.re_run)
                    b.evidence = self.host_url + '/badges/evidence?id=%d' % report.key().id()
                    b.put()
                    self.log.append('... ISSUED leader badge to %s, id=%d' % (email, b.key().id()))
            else:
                self.log.append('... WOULD ISSUE leader badge to %s' % ' '.join(emails))
        self._batch_write()

class BulkExpertLeaderIssueMapper(LoggingMapper):
    KIND = ExpertBadgeReport

    def __init__(self, really, course, part, host_url, re_run):
        super(BulkExpertLeaderIssueMapper, self).__init__()
        self.really = really
        self.course = course
        self.host_url = host_url
        self.re_run = re_run
        self.best_by_group = defaultdict(default_dict_entry)
        self.leader_badge_key = 'expert.leader'

        leader_badge = Badge.get_by_key_name(self.leader_badge_key)
        if not leader_badge:
            logging.warning('No badge with key_name: %s', self.leader_badge_key)
            self.log.append('No badge with key_name: %s'% self.leader_badge_key)
            if self.really:
                raise ValueError('No badge with key_name: %s' % self.leader_badge_key)

    def map(self, report):
        student = report.student
        self.log.append('---------------- Student %s' % student.key().name())

        if self.re_run:
            report._run(self.course)

        best_so_far = self.best_by_group[student.group_id][1]
        promotions = report.exemplary_count

        if promotions > best_so_far:
            self.log.append('New best for group %s, %d promotions' % (
                student.group_id, promotions))

            if report.is_complete:
                self.best_by_group[student.group_id] = ([student.key().name()], promotions)
            else:
                self.log.append('BUT, Skipping, not complete.')

        elif promotions == best_so_far:
            self.log.append('TIED best for group %s, %d promotions' % (
                student.group_id, promotions))

            if report.is_complete:
                self.best_by_group[student.group_id][0].append(student.key().name())
            else:
                self.log.append('BUT, Skipping, not complete.')

        return ([], [])

    def finish(self):
        if self.really:
            leader_badge = Badge.get_by_key_name(self.leader_badge_key)

        for group_id, (emails, count) in self.best_by_group.iteritems():
            self.log.append('Considering group %s, best score is %d' % (
                str(group_id), count))
            if count < 1:
                self.log.append('... Best score is too low, skipping.')
                continue
            if self.really:
                for email in emails:
                    b = Badge.issue(leader_badge,
                            db.Key.from_path(Student.kind(), email), put=False)
                    report = ExpertBadgeReport.on(
                            db.Key.from_path(Student.kind(), email),
                            course=self.course,
                            force_re_run=self.re_run)
                    b.evidence = self.host_url + '/badges/expert_evidence?id=%d' % report.key().id()
                    b.put()
                    self.log.append('... ISSUED leader badge to %s, id=%d' % (email, b.key().id()))
            else:
                self.log.append('... WOULD ISSUE leader badge to %s' % ' '.join(emails))
        self._batch_write()



issuer_mappers = {
        'completion': BulkIssueMapper,
        'leader': BulkLeaderIssueMapper,
        'expert': BulkExpertBadgeIssueMapper,
        'expert-leader': BulkExpertLeaderIssueMapper,
        }


class BulkIssuanceHandler(BaseHandler, ReflectiveRequestHandler):
    default_action = 'prep'
    get_actions = ['prep', 'watch']
    post_actions = ['start']

    TITLE = 'Bulk Issue Badges'

    class IssueForm(wtf.Form):
        part = wtf.IntegerField('Which part of the course to issue a badge for? (1,2,3)')
        really_save = wtf.BooleanField('Really issue the badges and freeze the scores?', default=False)
        leader_or_completion = wtf.RadioField('Do you want to issue completion badges, or leader badges?',
                choices=[(k, k) for k in issuer_mappers.keys()])
        force_re_run_reports = wtf.BooleanField('Re-run all unit and part reports? Will delete old ones if you also choose Really freeze above.', default=False)
        one_email = wtf.TextField('Only consider one student? Enter their e-mail here.',
                validators=[wtf.validators.Optional()])

    def _action_url(self, action, **kwargs):
        params = dict(kwargs)
        params['action'] = action
        return '?'.join((
            self.request.path,
            urllib.urlencode(params)))

    def get_prep(self):
        if not users.is_current_user_admin():
            self.abort(403)
        self.render_form(self.IssueForm())

    def render_form(self, form):
        self.template_value['form'] = form
        self.template_value['xsrf_token'] = self.create_xsrf_token('start')
        self.template_value['action_url'] = self._action_url('start')
        self.template_value['title'] = self.TITLE
        self.render('badge_bulk_issue.html')

    def post_start(self):
        if not users.is_current_user_admin():
            self.abort(403)

        form = self.IssueForm(self.request.POST)
        if not form.validate():
            self.render_form(form)
            return

        REALLY = form.really_save.data
        part_num = form.part.data

        problems = set()
        student_infos = []

        issuer = issuer_mappers[form.leader_or_completion.data]

        job = issuer(REALLY, self.get_course(), part_num, self.request.host_url, form.force_re_run_reports.data)
        if form.one_email.data:
            job.FILTERS.append(
                    ('__key__', db.Key.from_path('Student', form.one_email.data)))
            logging.debug('Filters for issuing: %s', repr(job.FILTERS))
        job_id = job.job_id
        deferred.defer(job.run, batch_size=50)
        self.redirect(self._action_url('watch', job_id=job_id))

    def get_watch(self):
        if not users.is_current_user_admin():
            self.abort(403)

        job_id = self.request.GET.get('job_id', None)
        if not job_id:
            self.abort(404)

        messages = BulkIssueMapper.logs_for_job(job_id)

        self.template_value['title'] = self.TITLE
        self.template_value['problems'] = []
        self.template_value['log'] = messages
        self.render('badge_bulk_issue_done.html')



class DammitMapper(LoggingMapper):
    """Goes through all PartReports and re-runs their assessment grades."""
    KIND = PartReport

    def __init__(self, course):
        super(DammitMapper, self).__init__()
        self.course = course

    def map(self, report):
        self.log.append("Working on report for %s, part %d" % (report.student_email, report.part))
        had_before = bool(report.assessment_scores)
        report._run_assessments(self.course)
        has_after = bool(report.assessment_scores)
        self.log.append("had before? %s.  has after? %s" % (had_before, has_after))

        return ([report], [])


class DammitHandler(BaseHandler, ReflectiveRequestHandler):
    get_actions = ['start', 'watch']
    default_action = 'watch'

    def _action_url(self, action, **kwargs):
        params = dict(kwargs)
        params['action'] = action
        return '?'.join((
            self.request.path,
            urllib.urlencode(params)))

    def get_start(self):
        if not users.is_current_user_admin():
            self.abort(403)

        course = self.get_course()
        job = DammitMapper(course)
        job_id = job.job_id
        deferred.defer(job.run, batch_size=50)
        self.redirect(self._action_url('watch', job_id=job_id))

    def get_watch(self):
        if not users.is_current_user_admin():
            self.abort(403)

        job_id = self.request.GET.get('job_id', None)
        if not job_id:
            self.abort(404)

        messages = BulkIssueMapper.logs_for_job(job_id)

        self.template_value['title'] = "GRRRRRR"
        self.template_value['problems'] = []
        self.template_value['log'] = messages
        self.render('badge_bulk_issue_done.html')
