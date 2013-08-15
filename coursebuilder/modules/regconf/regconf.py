import bleach
import wtforms as wtf
from modules.wikifolios.wiki_models import WikiPage
from models import custom_modules
from models.models import Student
from controllers.utils import BaseHandler, XsrfTokenManager
from google.appengine.ext import db
from google.appengine.api import users


class FormSubmission(db.Expando):
    form_name = db.StringProperty()
    user = db.ReferenceProperty(Student)
    submitted = db.DateTimeProperty(auto_now=True)


class PreAssignmentForm(wtf.Form):
    curricular_aim = wtf.TextAreaField("Curricular Aim", [wtf.validators.Length(min=10)])
    introduction = wtf.TextAreaField("Introduce Yourself")
    page = wtf.HiddenField(default="pre")


class ConfirmationForm(wtf.Form):
    participation_level = wtf.RadioField("Participation Level",
            choices=[
                ('badges', 'Badges'),
                ('instructor-cert', 'Instructor Certified'),
                ('for-credit', 'For Credit'),
                ])
    accept_terms = wtf.BooleanField("Terms of Use", validators=[wtf.validators.Required()])
    page = wtf.HiddenField(default="conf")


def on_pre_assignment_submission(handler, user, form):
    submission = FormSubmission(form_name='pre', user=user)
    form.populate_obj(submission)
    submission.put()

    allowed_tags = ['p', 'i', 'b', 'a']
    profile_page = WikiPage.get_page(user, unit=None, create=True)
    profile_page.text = bleach.clean(form.introduction.data,
            tags=allowed_tags)
    profile_page.put()

    handler.redirect('confirm?page=conf')


def on_confirmation_submission(handler, user, form):
    submission = FormSubmission(form_name='conf', user=user)
    form.populate_obj(submission)
    submission.put()

    user.is_participant = True
    user.put()

    handler.redirect("wikiprofile")


class ConfirmationHandler(BaseHandler):
    forms = {
            'pre': PreAssignmentForm,
            'conf': ConfirmationForm,
            }
    templates = {
            'pre': 'pre_assignment.html',
            'conf': 'confirm_registration.html',
            }
    actions = {
            'pre': on_pre_assignment_submission,
            'conf': on_confirmation_submission,
            }
    default_page = 'pre'

    def _page(self):
        page = self.default_page
        query_page = self.request.get('page', None)
        if query_page and query_page in self.templates.keys():
            page = query_page
        return page

    def get(self):
        app_user = self.get_user()
        if not app_user:
            # the request is anonymous
            self.redirect(
                users.create_login_url(self.request.uri), normalize=False)
            return
        user = self.personalize_page_and_get_enrolled()
        if not user:
            # there is a user, but they are not enrolled
            self.redirect('/register')
            return
        if user.is_participant:
            # the user has *already* filled out this form
            self.redirect('/course')
            return

        page = self._page()

        # submission may be None
        submission = FormSubmission.all().filter('form_name', page).filter('user', user.key()).order('-submitted').get()
        form = self.forms[page](None, submission)

        if 'redirect' in self.request.GET:
            self.template_value['is_redirect'] = True
        self.do_render(form, self.templates[page])

    def do_render(self, form, template):
        self.template_value['navbar'] = {'registration': True}
        self.template_value['form'] = form
        self.template_value['xsrf_token'] = (
            XsrfTokenManager.create_xsrf_token('register-conf-post-' + self._page()))
        self.render(template)

    def post(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            self.redirect('register')
            return
        if not self.assert_xsrf_token_or_fail(self.request, 'register-conf-post-' + self._page()):
            return

        page = self._page()

        form = self.forms[page](self.request.POST)
        if form.validate():
            self.actions[page](self, user, form)
        else:
            # Validation errors will be included in the 'form' object
            self.do_render(form, self.templates[page])


module = None

def register_module():
    global module

    handlers = [
            ('/confirm', ConfirmationHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("RegConf", "Registration Confirmation",
            [], handlers)

    return module

