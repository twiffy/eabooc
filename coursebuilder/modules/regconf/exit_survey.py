# -*- coding: utf-8 -*-
"""
A survey for the end of the course.
"""

import re
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
            for k,v in self.create_db_values(form.data):
                setattr(submission, k, v)
            submission.put()
            self.action(user, form)
        else:
            # Validation errors will be included in the 'form' object
            self.do_render(form)

    def create_db_values(self, form_dict):
        for k,v in form_dict.iteritems():
            if isinstance(v, dict):
                for inner_k, inner_v in self.create_db_values(v):
                    yield (
                            "-".join((k, inner_k)),
                            inner_v
                            )
            elif isinstance(v, basestring):
                yield (k, db.Text(v))
            else:
                yield (k, v)


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


class ExitSurveyIntroHandler(BaseHandler):
    def get(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return
        self.template_value['navbar'] = {}
        self.render('exit_survey_intro.html')


class ExitSurvey1Form(wtf.Form):
    first_hear = wtf.RadioField(
            "Where did you first hear about this course?<br>Select one.",
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
            "What factor most motivated you to <i>enroll</i> in this course?<br>Select one.",
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
            "What factor most motivated you to <i>complete</i> this course?<br>Select one.",
            choices=enroll_motivation.kwargs['choices'],
            validators=[wtf.validators.required()])
    complete_motivation_other = wtf.StringField(
            validators=[wtf.validators.optional()])


class ExitSurvey1Handler(SurveyHandler):
    form = ExitSurvey1Form
    template = 'exit_survey_1.html'
    name = 'exit_survey_1'

    def action(self, user, form):
        self.redirect("/survey2")


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
            "Which book format(s) did you use?<br>Check all that apply.",
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
        self.redirect("/survey3")


class ExitSurvey3Form(wtf.Form):
    hours_per_week = wtf.SelectField(
            "On average, how many hours per week did you spend on this course?",
            choices=[(str(n), str(n)) for n in range(1,31)],
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
        self.redirect('/survey4')

class ExitSurveyFeaturesForm(wtf.Form):
    field_pairs = []

feature_list = [
        u'...to initially define my curricular aim.', 
        u'...to be assigned to a networking group.', 
        u'...to redefine my curricular aim.', 
        u'...to redefine my context and role.', 
        u'...to read the chapters.', 
        u'...to rank concepts.', 
        u'...to find outside resources.', 
        u'...to write big ideas.', 
        u'...to write reflections.', 
        u'...to endorse others.', 
        u'...to receive endorsements.', 
        u'...to promote others.', 
        u'...to receive promotions.', 
        u'...to post questions for others on my wikifolio.', 
        u'...to give comments.', 
        u'...to reply to comments.', 
        u'...to receive notifications.', 
        u'...to complete exams.', 
        u'...to get early feedback before a wiki was due.', 
        u'...to get instructor observations after wikis were completed.', 
        u'...to get announcements in-course.', 
        u'...to use the discussion forum.', 
        u'...to extend/change my name to reflect my identity and role.', 
        u'...to see others’ names on the participant list with their role.', 
        u'...to use the formatting and styling functions of the wikifolio editor.', 
        u'...to have a public profile “My Wikifolio” page with an introduction.', 
        u'...to read the Remediating Assessment blog.', 
        ]

LIKERT_CHOICES = [
        (a, a) for a in ('1', '2', '3', '4', '5', 'na', 'idk')]
likert_kwargs = {
        'validators': [wtf.validators.optional()],
        'choices': LIKERT_CHOICES
        }
comment_kwargs = {
        'validators': [wtf.validators.optional()],
        }

class LikertItemForm(wtf.Form):
    rating = wtf.RadioField(**likert_kwargs)
    comment = wtf.StringField(**comment_kwargs)

for feature in feature_list:
    field_name = re.sub('[^\w\s]', '', feature)
    field_name = re.sub('[\s]+', '_', field_name)

    setattr(ExitSurveyFeaturesForm, field_name,
            wtf.FormField(LikertItemForm, feature))


class ExitSurveyFeaturesHandler(SurveyHandler):
    form = ExitSurveyFeaturesForm
    template = 'exit_survey_features.html'
    name = 'exit_survey_features'

    def action(self, user, form):
        self.redirect("/course")

all_exit_forms = [
        ExitSurvey1Form,
        ExitSurvey2Form,
        ExitSurvey3Form,
        ExitSurveyFeaturesForm
        ]

all_exit_form_db_fields = []
for normal_form in all_exit_forms[0:3]:
    all_exit_form_db_fields.extend(
            [f.name for f in normal_form()])

for field in ExitSurveyFeaturesForm():
    all_exit_form_db_fields.append(field.name + '-rating')
    all_exit_form_db_fields.append(field.name + '-comment')
