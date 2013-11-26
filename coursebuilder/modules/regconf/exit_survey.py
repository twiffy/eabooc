from regconf import FormSubmission
from controllers.utils import BaseHandler, XsrfTokenManager
import webapp2
from google.appengine.ext import db
import wtforms as wtf

class SurveyHandler(BaseHandler):
    form = None
    template = None
    name = None

    def action(self, user, form):
        raise NotImplemented()

    def get(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return

        sub_query = FormSubmission.all()
        sub_query.filter('form_name', self.name)
        sub_query.filter('user', user.key())
        prev_submission = sub_query.order('-submitted').get()

        form = self.form(None, prev_submission)

        self.do_render(form)

    def do_render(self, form):
        self.template_value['navbar'] = {}
        self.template_value['form'] = form
        self.template_value['post_url'] = self.request.url
        self.template_value['xsrf_token'] = (
            XsrfTokenManager.create_xsrf_token('survey-post-' + self.name))
        self.render(self.template)

    def post(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return
        if not self.assert_xsrf_token_or_fail(self.request, 'survey-post-' + self.name):
            return

        form = self.form(self.request.POST)
        if form.validate():
            submission = FormSubmission(form_name=self.name, user=user)
            for k,v in form.data.items():
                setattr(submission, k, db.Text(v))
            submission.put()
            self.action(self, user, form)
        else:
            # Validation errors will be included in the 'form' object
            self.do_render(form, self.templates[page])

class TryhardForm(wtf.Form):
    a = wtf.IntegerField()

class TryhardSurveyHandler(SurveyHandler):
    form = TryhardForm
    template = 'try.html'
    name = 'tryhard'

    def action(self, user, form):
        print "YAY", form.data
