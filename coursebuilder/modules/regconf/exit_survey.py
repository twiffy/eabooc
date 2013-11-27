# -*- coding: utf-8 -*-

from regconf import FormSubmission
from controllers.utils import BaseHandler, XsrfTokenManager
import webapp2
from google.appengine.ext import db
import wtforms as wtf

reuse_previous_submissions = False

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

        if reuse_previous_submissions:
            sub_query = FormSubmission.all()
            sub_query.filter('form_name', self.name)
            sub_query.filter('user', user.key())
            prev_submission = sub_query.order('-submitted').get()
        else:
            prev_submission = None

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
            self.action(user, form)
        else:
            # Validation errors will be included in the 'form' object
            self.do_render(form)

class TryhardForm(wtf.Form):
    first_hear = wtf.RadioField(
            "Where did you first hear about this course?",
            choices=(
                ('facebook', 'Facebook'),
                ('twitter', 'Twitter'),
                ('linkedin', 'LinkedIn'),
                ('google-ads', 'Google Ads'),
                ('hastac', 'HASTAC'),
                ('word-of-mouth', 'Word of Mouth (please explain)'),
                ('other', 'Other (please explain)'),
                ),
            validators=(wtf.validators.required(),))
    first_hear_explain = wtf.StringField(
            validators=[wtf.validators.optional()])

    other_courses = wtf.RadioField(
            "Before enrolling in this course, had you enrolled in another online course?",
            choices=(
                ('yes', 'Yes'),
                ('no', 'No'),
                ),
            validators=[wtf.validators.required()])
    other_courses_how_many = wtf.SelectField(
            "If so, how many?",
            choices=(
                [(str(n), str(n)) for n in range(1,11)]
                + [('11+', '11 or more')]),
            validators=[wtf.validators.optional()])
    other_courses_what = wtf.TextAreaField(
            "If so, what courses and where?",
            validators=[wtf.validators.optional()])

    enroll_motivation = wtf.RadioField(
            "What factor most motivated you to <i>enroll</i> in this course?",
            choices=(
                ('expert-badges', 'Earning assessment expert & expertise badges'),
                ('leader-badges', 'Earning assessment leader badges'),
                ('certificate', 'Earning the instructor verified certificate'),
                ('required', 'I was required to by my job'),
                ('peers', 'Interacting with peers about assessment'),
                ('instructor', u'The instructor’s reputation '),
                ('learning', 'Learning about assessment   '),
                ('taking-mooc', 'Taking an open online course'),
                ('other', 'Other (please specify)'),
                ),
            validators=[wtf.validators.required()])
    enroll_motivation_other = wtf.StringField(
            validators=[wtf.validators.optional()])

    complete_motivation = wtf.RadioField(
            "What factor most motivated you to <i>complete</i> this course?",
            choices=enroll_motivation.kwargs['choices'],
            validators=[wtf.validators.required()])
    complete_motivation_other = wtf.StringField(
            validators=[wtf.validators.optional()])


class TryhardSurveyHandler(SurveyHandler):
    form = TryhardForm
    template = 'try.html'
    name = 'tryhard'

    def action(self, user, form):
        print "YAY", form.data
