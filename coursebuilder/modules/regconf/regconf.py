import wtforms as wtf
from models import custom_modules
from models.models import Student
from controllers.utils import BaseHandler, XsrfTokenManager
from google.appengine.ext import db

class FirstAssignmentPage(wtf.Form):
    # TODO: how to add ckeditor, how to add more text
    # how to make big textarea
    curricular_aim = wtf.TextAreaField("Curricular Aim", [wtf.validators.Length(min=10)])
    professional_role = wtf.TextAreaField("Professional Role")
    introduction = wtf.TextAreaField("Introduce Yourself")

class FormSubmission(db.Expando):
    form_name = db.StringProperty()
    user = db.ReferenceProperty(Student)
    submitted = db.DateTimeProperty(auto_now=True)

class ConfirmationForm:
    pass

def on_pre_assignment_submission(handler, user, form):
    submission = FormSubmission(form_name='pre', user=user)
    form.populate_obj(submission)
    submission.put()

    user.is_participant = True
    user.put()

    handler.redirect('course')

class ConfirmationHandler(BaseHandler):
    forms = {
            'pre': FirstAssignmentPage,
            'conf': ConfirmationForm,
            }
    templates = {
            'pre': 'confirm_registration.html',
            'conf': 'nothing_yet.html',
            }
    actions = {
            'pre': on_pre_assignment_submission,
            'conf': None,
            }
    default_page = 'pre'

    def _page(self):
        page = self.default_page
        query_page = self.request.get('page', None)
        if query_page and query_page in self.templates.keys():
            page = query_page
        return page

    def get(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            self.redirect('register')
            return

        page = self._page()

        # submission may be None
        submission = FormSubmission.all().filter('form_name', page).filter('user', user.key()).get()
        form = self.forms[page](None, submission)

        if 'redirect' in self.request.GET:
            self.template_value['is_redirect'] = True
        self.do_render(form, self.templates[page])

    def do_render(self, form, template):
        self.template_value['navbar'] = {'confirm': True}
        self.template_value['form'] = form
        self.template_value['xsrf_token'] = (
            XsrfTokenManager.create_xsrf_token('register-conf-post'))
        self.render(template)

    def post(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            self.redirect('register')
            return
        if not self.assert_xsrf_token_or_fail(self.request, 'register-conf-post'):
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

