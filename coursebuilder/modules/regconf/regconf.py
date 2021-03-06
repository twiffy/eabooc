"""
Code to confirm people's registrations, and ask them tons of questions.
"""
import bleach
import wtforms as wtf
from modules.wikifolios.wiki_models import WikiPage
from models import custom_modules
from models.models import Student
from controllers.utils import BaseHandler, XsrfTokenManager
from google.appengine.ext import db
from google.appengine.api import users
from common import mailchimp
import logging
from common import generalcounter

# If true, don't redirect students away from the confirmation pages, even if
# they are already fully registered.
DEBUG_CONFIRMATION = False

class FormSubmission(db.Expando):
    form_name = db.StringProperty()
    user = db.ReferenceProperty(Student)
    submitted = db.DateTimeProperty(auto_now=True)


class PreAssignmentForm(wtf.Form):
    curricular_aim = wtf.TextAreaField("Curricular Aim", [wtf.validators.Length(min=10)])
    introduction = wtf.TextAreaField("Introduce Yourself", [wtf.validators.Length(min=10)])
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
    book_option = wtf.RadioField("Book Option",
            validators=[wtf.validators.Optional()],
            choices=[
                ('paperback-7th', '7th edition paperback (2014, currently $93 new at Amazon, $110 at Pearson)'),
                ('coursesmart', '''7th edition e-text from CourseSmart (currently 180-day rental with options to print, $42).
                    International Students, please use <a href=
                    "http://www.coursesmart.co.uk/classroom-assessment-what-teachers-need-to/w-james-popham/dp/9780133492514"
                    target="_blank">CourseSmart UK</a>.'''),
                ('paperback-6th', '6th edition paperback (2010, currently $14 used on Amazon)'),
                ('no-book', 'No book (this will make the course very difficult!)'),
                ])
    book_other = wtf.TextField()
    accept_location = wtf.BooleanField("Location", default=True)

MAXIMUM_PARTICIPANTS = 500
PARTICIPANT_COUNT = "participant-count"
def get_student_count():
    count = generalcounter.get_count(PARTICIPANT_COUNT)
    if not count:
        count = Student.all(keys_only=True).filter("is_participant", True).count(limit=10000)
        generalcounter.increment(PARTICIPANT_COUNT, by=count)
    return count

def inc_student_count():
    generalcounter.increment(PARTICIPANT_COUNT)


def on_pre_assignment_submission(handler, user, form):
    submission = FormSubmission(form_name='pre', user=user)
    for k,v in form.data.items():
        setattr(submission, k, db.Text(v))
    submission.put()

    allowed_tags = ['p', 'i', 'b', 'a', 'br']
    profile_page = WikiPage.get_page(user, unit=None, create=True)
    profile_page.text = db.Text(bleach.clean(form.introduction.data,
            tags=allowed_tags))
    profile_page.put()

    handler.redirect('confirm?page=conf')


def on_confirmation_submission(handler, user, form):
    submission = FormSubmission(form_name='conf', user=user)
    form.populate_obj(submission)
    submission.put()

    user.ensure_wiki_id()
    user.is_participant = True
    user.put()

    mailchimp.subscribe('confirmed', user.key().name(), user.name)
    if form.participation_level.data == u'for-credit':
        mailchimp.subscribe('for-credit', user.key().name(), user.name)
    mailchimp.unsubscribe('pre-reg', user.key().name())
    inc_student_count()

    handler.redirect("wikiprofile?confirm=1&student=%d" % user.wiki_id)


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

    def course_is_full(self):
        can_register = self.app_context.get_environ(
                )['reg_form']['can_register']
        return (not can_register) or get_student_count() >= MAXIMUM_PARTICIPANTS

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
        if self.course_is_full():
            self.render_full_course_sadness_page()
            return
        if not user:
            # there is a user, but they are not enrolled
            self.redirect('/register')
            return
        if user.is_participant and not DEBUG_CONFIRMATION:
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
        self.template_value['list'] = list
        self.template_value['max_student_count'] = MAXIMUM_PARTICIPANTS
        self.template_value['student_count'] = get_student_count()
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
        if self.course_is_full():
            self.render_full_course_sadness_page()
            return

        page = self._page()

        form = self.forms[page](self.request.POST)
        if form.validate():
            self.actions[page](self, user, form)
        else:
            # Validation errors will be included in the 'form' object
            self.do_render(form, self.templates[page])

    def render_full_course_sadness_page(self):
        self.template_value['course_status'] = 'full'
        self.template_value['navbar'] = {'registration': True}
        self.render('confirmation.html')


class StudentCountHandler(BaseHandler):
    def get(self):
        self.response.write('''
            <html><body>
            <center>
            Current participant count is:<br>
            <h1 style="font-size: 1000%;">''')

        count = get_student_count()
        self.response.write(count)
        self.response.write('''
            </h1>
            </center></body></html>
            ''')




module = None

def register_module():
    global module

    import exit_survey
    handlers = [
            ('/confirm', ConfirmationHandler),
            ('/enrollment', StudentCountHandler),
            ('/survey', exit_survey.ExitSurveyIntroHandler),
            ('/survey1', exit_survey.ExitSurvey1Handler),
            ('/survey2', exit_survey.ExitSurvey2Handler),
            ('/survey3', exit_survey.ExitSurvey3Handler),
            ('/survey4', exit_survey.ExitSurveyFeaturesHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("RegConf", "Registration Confirmation",
            [], handlers)

    return module

