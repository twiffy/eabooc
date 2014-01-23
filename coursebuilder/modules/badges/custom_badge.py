from google.appengine.ext import db
import logging
from urlparse import urljoin
from models.roles import Roles
import urllib
from badge_models import *
import wtforms as wtf
from wtforms.ext.appengine.db import model_form
from markupsafe import Markup
from controllers.utils import BaseHandler, ReflectiveRequestHandler
from models.models import Student
from google.appengine.api import users
from modules.wikifolios.wiki_models import Annotation, WikiPage
from modules.wikifolios.report import PartReport

UNIT_NUMBER = 12

BadgeForm = model_form(Badge)

class CommentsForm(wtf.Form):
    public_comments = wtf.TextAreaField(
            '''Public comments, which will be shown at the top of the term paper.''')
    review_source = wtf.TextField(
            "E-mail address of the user who the public comments came from")

def custom_badge_name(student):
    return 'paper.%d' % student.wiki_id

not_specified = object()
class CustomBadgeEditHandler(BaseHandler, ReflectiveRequestHandler):
    get_actions = ['edit']
    post_actions = ['save']
    default_action = 'edit'

    def _action_url(self, action, email=not_specified):
        if email is not_specified:
            email = self.request.GET['email']
        params = {
                'email': email,
                'action': action,
                }
        return '?'.join((
            self.request.path,
            urllib.urlencode(params)))

    def get_edit(self):
        if not Roles.is_course_admin(self.app_context):
            self.abort(403, 'You are not an admin :(')

        student_email = self.request.GET.get('email', None)
        if not student_email:
            self.abort(404, 'email= parameter required')
        student = Student.get_enrolled_student_by_email(student_email)
        if not student:
            self.abort(404, Markup('Could not find a student with email "%s"') % student_email)
        
        badge = Badge.get_or_insert(
                custom_badge_name(student))

        badge_form = BadgeForm(None, badge)
        review = Annotation.reviews(whose=student, unit=UNIT_NUMBER).get()
        comments_form = CommentsForm()
        if review:
            logging.debug('Found a review: %s', review.reason[:30])
            comments_form.public_comments = review.reason
            comments_form.review_source = review.who.key().name()
        else:
            logging.debug('Did not found no review')
        self.render_edit(badge_form, comments_form)

    def render_edit(self, badge_form, comments_form):
        self.template_value['action_url'] = self._action_url
        self.template_value['forms'] = [badge_form, comments_form]
        self.template_value['xsrf_token'] = self.create_xsrf_token('save')
        self.template_value['title'] = 'Edit custom badge'
        self.render('custom_badge.html')

    def post_save(self):
        if not Roles.is_course_admin(self.app_context):
            self.abort(403, 'You are not an admin :(')
        user = self.personalize_page_and_get_enrolled()

        student_email = self.request.GET.get('email', None)
        if not student_email:
            self.abort(404, 'email= parameter required')
        student = Student.get_enrolled_student_by_email(student_email)
        if not student:
            self.abort(404, Markup('Could not find a student with email "%s"') % student_email)

        badge_slug = custom_badge_name(student)
        badge = Badge.get_or_insert(badge_slug)

        badge_form = BadgeForm(self.request.POST, badge)
        comments_form = CommentsForm(self.request.POST)
        if not (badge_form.validate() and comments_form.validate()):
            self.render_edit(badge_form, comments_form)
            return

        comments_form.validate()
        reviewer = Student.get_by_email(comments_form.review_source.data)
        if not reviewer:
            comments_form.review_source.errors.append("Could not find a user with that e-mail address")
            self.render_edit(badge_form, comments_form)
            return

        page = WikiPage.get_page(student, unit=UNIT_NUMBER)
        if not page:
            self.abort(404, Markup('Could not find unit %d wikifolio for student "%s"') % (UNIT_NUMBER, student_email))

        old_reviews = Annotation.reviews(whose=student, unit=UNIT_NUMBER).run()
        db.delete(old_reviews)
        Annotation.review(page, who=reviewer, text=comments_form.public_comments.data)

        if not Annotation.endorsements(what=page, who=user).count(limit=1):
            Annotation.endorse(page, who=user, optional_done=True)
        
        badge_form.populate_obj(badge)
        badge.put()

        report = PartReport.on(student, self.get_course(), 4, force_re_run=True, put=False)
        for rep in report.unit_reports:
            rep._run()
            rep.put()
        report.slug = badge_slug
        report.put()
        assertion = Badge.issue(badge, student, put=False)
        assertion.evidence = urljoin(self.request.host_url, '/badges/evidence?id=%d' % report.key().id())
        assertion.put()
        self.response.write(
                Markup("Issued badge %s to %s, evidence %s") % (
                    badge.key().name(), student_email, assertion.evidence))
