from controllers.utils import BaseHandler, ReflectiveRequestHandler
from collections import defaultdict
from models import transforms
from modules.badges.badge_models import Badge, BadgeAssertion
from report import UnitReport, PartReport
from report import _parts as part_config
from models.models import Student
from jinja2 import Markup
import urllib
import wtforms as wtf
from google.appengine.api import users
import page_templates


class EvidenceHandler(BaseHandler):
    def get(self):
        try:
            report = PartReport.get_by_id(int(self.request.GET.get('id', -1)))
        except ValueError:
            report = None
        if not report:
            self.abort(404)

        self.report = report
        self.template_value['navbar'] = {}
        self.template_value['author'] = self.report.student
        self.template_value['unit_link'] = self._unit_link

        try:
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

    def render_unit(self):
        self.template_value['fields'] = {
                k: Markup(v) for k,v in transforms.loads(self.unit.wiki_fields).iteritems()}
        self.template_value['unit'] = self.find_unit_by_id(self.unit_num)
        self.template_value['report'] = self.unit
        self.template_value['layout_template'] = 'wf_evidence.html'
        self.render(page_templates.templates[self.unit_num])

    def render_top(self):
        self.template_value['part'] = self.report
        self.render('wf_evidence_top.html')


class BulkIssuanceHandler(BaseHandler, ReflectiveRequestHandler):
    default_action = 'prep'
    get_actions = ['prep']
    post_actions = ['start']

    TITLE = 'Bulk Issue Badges'

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
        self.issue_badges(REALLY, part_num, problems, student_infos)
        self.template_value['title'] = self.TITLE
        self.template_value['problems'] = problems
        self.template_value['log'] = student_infos
        self.render('badge_bulk_issue_done.html')

    def issue_badges(self, REALLY, part_num, problems, student_infos):
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
                    b = Badge.issue(badge, student, put=False) # need to include evidence URL here somehow
                    b.evidence = self.request.host_url + '/badges/evidence?id=%d' % report.key().id()
                    b.put()

                    student_infos.append(Markup(' Issued badge, assertion id=%d') % b.key().id())
                else:
                    student_infos.append(' WOULD issue badge.')

NOBODY = object()
class BulkLeaderIssuanceHandler(BulkIssuanceHandler):
    TITLE = 'Bulk Issue LEADER Badges'

    def issue_badges(self, REALLY, part_num, problems, student_infos):
        best_by_group = defaultdict(
                lambda: ([NOBODY], -1))

        leader_badge_key = part_config[part_num]['slug'] + '.leader'
        leader_badge = Badge.get_by_key_name(leader_badge_key)
        if not leader_badge:
            problems.add(Markup('No badge with key_name: %s') % leader_badge_key)
            if REALLY:
                return

        for student in Student.all().filter('is_participant', True).run():
            student_infos.append(Markup('<p>Student %s') % student.key().name())

            part_report = PartReport.on(student, course=self.get_course(), part=part_num)
            if not part_report.is_complete:
                student_infos.append(Markup(' Skipping, since not complete.'))
                continue

            student_infos.append(' .. Part is complete, considering units.')

            unit_reports = part_report.unit_reports
            promotions = 0

            for ur in unit_reports:
                promotions += ur.promotions

            if promotions > best_by_group[student.group_id][1]:
                best_by_group[student.group_id] = ([student.key().name()], promotions)

                student_infos.append(Markup(' They have current best for group %s, with %d.') % (
                    student.group_id, promotions))

            elif promotions == best_by_group[student.group_id][1]:
                best_by_group[student.group_id][0].append(student.key().name())

                student_infos.append(Markup(' They <b>ARE TIED for current best</b> for group %s, with %d.') % (
                    student.group_id, promotions))

        for group_id, (emails, count) in best_by_group.iteritems():
            student_infos.append(Markup('<p>Considering group %s') % str(group_id))
            if REALLY:
                for email in emails:
                    a = Badge.issue(leader_badge, email)
                    student_infos.append(Markup('... ISSUED leader badge to %s, id=%d') % (email, a.key().id()))
            else:
                student_infos.append(Markup('... WOULD ISSUE leader badge to %s') % ' '.join(emails))
