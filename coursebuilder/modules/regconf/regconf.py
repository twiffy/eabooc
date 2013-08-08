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

class FormProgress(db.Expando):
    form_name = db.StringProperty()
    user = db.ReferenceProperty(Student)

class ConfirmationHandler(BaseHandler):
    def get(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            self.redirect('register')
            return
        progress = FormProgress.all().filter('form_name', 'FirstAssignmentPage').filter('user', user.key()).get()
        form = FirstAssignmentPage(None, progress)
        self.do_render(form)

    def do_render(self, form):
        self.template_value['navbar'] = {'confirm': True}
        self.template_value['form'] = form
        self.template_value['xsrf_token'] = (
            XsrfTokenManager.create_xsrf_token('register-conf-post'))
        self.render("confirm_registration.html")

    def post(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            self.redirect('register')
            return
        if not self.assert_xsrf_token_or_fail(self.request, 'register-conf-post'):
            return

        form = FirstAssignmentPage(self.request.POST)
        if form.validate():
            progress = FormProgress(form_name='FirstAssignmentPage', user=user)
            form.populate_obj(progress)
            progress.put()
            self.redirect('course')
        else:
            self.do_render(form)

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

