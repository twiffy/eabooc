from google.appengine.ext import db
import urllib
from badge_models import *
import wtforms as wtf
from wtforms.ext.appengine.db import model_form
from markupsafe import Markup
from controllers.utils import BaseHandler, ReflectiveRequestHandler
from models.models import Student
from google.appengine.api import users
from modules.wikifolios.wiki_models import Annotation, WikiPage

UNIT_NUMBER = 12

BadgeForm = model_form(Badge)

class CommentsForm(wtf.Form):
    public_comments = wtf.TextAreaField(
            '''Public comments, which will be shown at the top of the term paper.''')

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
        if not users.is_current_user_admin():
            self.abort(403, 'You are not an admin :(')

        student_email = self.request.GET.get('email', None)
        if not student_email:
            self.abort(404, 'email= parameter required')
        student = Student.get_enrolled_student_by_email(student_email)
        if not student:
            self.abort(404, Markup('Could not find a student with email "%s"') % student_email)
        
        #import pdb
        #pdb.set_trace()
        badge = Badge.get_or_insert(
                custom_badge_name(student))

        badge_form = BadgeForm(None, badge)
        review = Annotation.reviews(whose=student, unit=UNIT_NUMBER).get()
        comments_form = CommentsForm()
        if review:
            comments_form.public_comments = review.reason

        self.template_value['action_url'] = self._action_url
        self.template_value['forms'] = [badge_form, comments_form]
        self.template_value['xsrf_token'] = self.create_xsrf_token('save')
        self.template_value['title'] = 'Edit custom badge'
        self.render('custom_badge.html')

    def post_save(self):
        if not users.is_current_user_admin():
            self.abort(403, 'You are not an admin :(')

        self.response.write("OHAI")
