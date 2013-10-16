from controllers.utils import BaseHandler, ReflectiveRequestHandler
from modules.badges.badge_models import Badge, BadgeAssertion
from report import UnitReport, PartReport
from models.models import Student
from jinja2 import Markup
import urllib
import wtforms as wtf
from google.appengine.api import users


class EvidenceHandler(BaseHandler):
    def get(self):
        try:
            assertion = BadgeAssertion.get_by_id(int(self.request.GET.get('assertion', -1)))
        except ValueError:
            assertion = None
        if not assertion:
            self.abort(404)

        self.response.write('hi')

        #OK, so maybe something needs to live in the DB that "is" the evidence.
        # It needs to at least give enough info that you can make a PartReport.
        # Can I put something in the badges/ part that is fairly open-ended?


class UnitReportHandler(BaseHandler):
    def get(self):
        try:
            report = UnitReport.get_by_id(int(self.request.GET.get('report', -1)))
        except ValueError:
            report = None
        if not report:
            self.abort(404)

        self.response.write('hi')


class BulkIssuanceHandler(BaseHandler, ReflectiveRequestHandler):
    default_action = 'prep'
    get_actions = ['prep']
    post_actions = ['start']

    def _action_url(self, action):
        params = {
                'action': action,
                }
        return '?'.join((
            self.request.path,
            urllib.urlencode(params)))

    class IssueForm(wtf.Form):
        part = wtf.IntegerField('Which part of the course to issue a badge for? (1,2,3)')
        really_save = wtf.BooleanField('Really issue the badges and freeze the scores?', default=False)

    def get_prep(self):
        if not users.is_current_user_admin():
            self.abort(403)
        self.render_form(self.IssueForm())

    def render_form(self, form):
        self.template_value['form'] = form
        self.template_value['xsrf_token'] = self.create_xsrf_token('start')
        self.template_value['action_url'] = self._action_url('start')
        self.template_value['title'] = 'Bulk Issue Badges'
        self.render('badges_bulk_issue.html')

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
        for student in Student.all().filter('is_participant', True).run():
            student_infos.append(Markup('<p>Student %s') % student.key().name())

            report = PartReport.on(student, course=self.get_course(), part=part_num)
            if REALLY:
                report.put_all()
            student_infos.append(Markup(' Passed? %s.') % report.is_complete)

            badge = report.badge
            if not badge:
                problems.add('There is no badge with key_name %s (so I cannot issue a badge)' % report.slug)
                continue

            if report.is_complete:
                if REALLY:
                    b = Badge.issue(badge, student) # need to include evidence URL here somehow
                    student_infos.append(Markup(' Issued badge, assertion id=%d') % b.key().id())
                else:
                    student_infos.append(' WOULD issue badge.')

        self.template_value['problems'] = problems
        self.template_value['log'] = student_infos
        self.render('badge_bulk_issue_done.html')
