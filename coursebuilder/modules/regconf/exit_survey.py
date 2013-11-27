# -*- coding: utf-8 -*-

from regconf import FormSubmission
from controllers.utils import BaseHandler, XsrfTokenManager
import webapp2
from google.appengine.ext import db
import wtforms as wtf
from wtforms.widgets.core import html_params
from markupsafe import Markup

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
                if isinstance(v, basestring):
                    setattr(submission, k, db.Text(v))
                else:
                    setattr(submission, k, v)
            submission.put()
            self.action(user, form)
        else:
            # Validation errors will be included in the 'form' object
            self.do_render(form)


class HorizontalWidget(object):
    def __init__(self, html_tag):
        self.html_tag = html_tag

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        html = ['<%s %s>' % (self.html_tag, html_params(**kwargs))]
        for subfield in field:
            html.append(unicode(subfield()))
            html.append(u' ')
            html.append(unicode(subfield.label))
            html.append(u' ')
        html.append('</%s>' % self.html_tag)
        return Markup(''.join(html))


class ExitSurvey1Form(wtf.Form):
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


class ExitSurvey1Handler(SurveyHandler):
    form = ExitSurvey1Form
    template = 'exit_survey_1.html'
    name = 'exit_survey_1'

    def action(self, user, form):
        print "YAY", form.data


class MultiCheckboxField(wtf.SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = wtf.widgets.ListWidget(prefix_label=False)
    option_widget = wtf.widgets.CheckboxInput()


class ExitSurvey2Form(wtf.Form):
    book_format = MultiCheckboxField(
            "Which book format(s) did you use?",
            choices=(
                ('book-7th', 'Hard copy of Popham (Seventh Edition)'),
                ('book-6th', 'Hard copy of Popham (Sixth Edition)'),
                ('book-5th', 'Hard copy of Popham (Fifth Edition)'),
                ('ebook', 'E-text of Popham'),
                ('other-online', 'Other Online Resources (please explain)'),
                ('no-book', 'I did not use the book (please explain)'),
                ),
            validators=[wtf.validators.required()])
    book_format_explain = wtf.StringField(
            validators=[wtf.validators.optional()])

    required_to_take = wtf.RadioField(
            "Were you required by someone to complete this course?  If so, please explain.",
            choices=(
                ('yes', 'Yes'),
                ('no', 'No'),
                ),
            widget=HorizontalWidget('div'),
            validators=[wtf.validators.required()])
    required_to_take_explain = wtf.StringField(
            validators=[wtf.validators.optional()])

    professional_development = wtf.RadioField(
            """Did this course count towards a professional development 
            requirement for your job?  If so, please explain.""",
            choices=(
                ('yes', 'Yes'),
                ('no', 'No'),
                ),
            widget=HorizontalWidget('div'),
            validators=[wtf.validators.required()])
    professional_development_explain = wtf.StringField(
            validators=[wtf.validators.optional()])

    # TODO professional role

    shared_any_badges = wtf.RadioField(
            """Did you share any digital badges from this course?  If so, describe your experience.""",
            choices=(
                ('yes', 'Yes'),
                ('no', 'No'),
                ),
            widget=HorizontalWidget('div'),
            validators=[wtf.validators.required()])
    shared_badges_experience = wtf.TextAreaField(
            validators=[wtf.validators.optional()])

    claimed_badges_mozilla = wtf.RadioField(
            """Did you claim any badges on Mozilla OBI from this course?""",
            choices=(
                ('yes', 'Yes'),
                ('no', 'No'),
                ),
            widget=HorizontalWidget('div'),
            validators=[wtf.validators.required()])
    
    course_badges_price = wtf.StringField(
            """Now that you have taken the course, how much do you think you
            might have paid to take the course and earn digital badges?""",
            validators=[wtf.validators.required()])
    certificate_price = wtf.StringField(
            """Now that you have taken the course, how much do you think you
            might have paid to earn the instructor verified Certificate?""",
            validators=[wtf.validators.required()])


class ExitSurvey2Handler(SurveyHandler):
    form = ExitSurvey2Form
    template = 'exit_survey_2.html'
    name = 'exit_survey_2'

    def action(self, user, form):
        print "YAY", form.data


class ExitSurvey3Form(wtf.Form):
    hours_per_week = wtf.SelectField(
            "On average, how many hours per week did you spend on this course?",
            choices=(
                [(str(n), str(n)) for n in range(1,16)]
                + [
                    ('16-20', '16 to 20'),
                    ('21-25', '21 to 25'),
                    ('26-30', '26 to 30'),
                    ('30+', 'more than 30'),
                    ]),
            validators=[wtf.validators.required()])

    most_favorite = wtf.TextAreaField(
            "What was your most favorite part about the course?",
            validators=[wtf.validators.required()])

    least_favorite = wtf.TextAreaField(
            "What was your least favorite part about the course?",
            validators=[wtf.validators.required()])

    suggestions = wtf.TextAreaField(
            "What suggestions do you have for improving the course?",
            validators=[wtf.validators.required()])

    would_recommend = wtf.RadioField(
            """Would you recommend this course to a colleague?""",
            choices=(
                ('yes', 'Yes'),
                ('no', 'No'),
                ),
            widget=HorizontalWidget('div'),
            validators=[wtf.validators.required()])

    # TODO recommend to a colleague via email


class ExitSurvey3Handler(SurveyHandler):
    form = ExitSurvey3Form
    template = 'exit_survey_3.html'
    name = 'exit_survey_3'

    def action(self, user, form):
        print "YAY", form.data
