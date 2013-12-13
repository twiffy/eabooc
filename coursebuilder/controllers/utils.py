# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Handlers that are not directly related to course content."""

__author__ = 'Saifu Angto (saifu@google.com)'

import base64
import hmac
import os
import time
import urlparse
import re
import logging
import appengine_config
from models import transforms
from models.config import ConfigProperty
from models.config import ConfigPropertyEntity
from models.courses import Course
from models.models import Student
from models.models import EventEntity
from models.roles import Roles
import webapp2
from google.appengine.api import namespace_manager
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext.db import BadValueError
from common import mailchimp
import modules.badges.util
from modules.wikifolios.report import PartReport, ExpertBadgeReport
import wtforms as wtf

# The name of the template dict key that stores a course's base location.
COURSE_BASE_KEY = 'gcb_course_base'

# The name of the template dict key that stores data from course.yaml.
COURSE_INFO_KEY = 'course_info'

XSRF_SECRET_LENGTH = 20

XSRF_SECRET = ConfigProperty(
    'gcb_xsrf_secret', str, (
        'Text used to encrypt tokens, which help prevent Cross-site request '
        'forgery (CSRF, XSRF). You can set the value to any alphanumeric text, '
        'preferably using 16-64 characters. Once you change this value, the '
        'server rejects all subsequent requests issued using an old value for '
        'this variable.'),
    'course builder XSRF secret')


# Whether to record page load/unload events in a database.
CAN_PERSIST_PAGE_EVENTS = ConfigProperty(
    'gcb_can_persist_page_events', bool, (
        'Whether or not to record student page interactions in a '
        'datastore. Without event recording, you cannot analyze student '
        'page interactions. On the other hand, no event recording reduces '
        'the number of datastore operations and minimizes the use of Google '
        'App Engine quota. Turn event recording on if you want to analyze '
        'this data.'),
    False)

def _ga_key_sanity_check(value, errors):
    if not value:
        return
    if not re.match(r'UA-\d+-\d+', value):
        errors.append("Doesn't look like a google analytics key ('UA-#####-#')")

GOOGLE_ANALYTICS_KEY = ConfigProperty(
    'ga_analytics_key', str, (
        'The Google Analytics key to use for this course.  Should be'
        'a string like UA-12345678-1.'),
    '', validator=_ga_key_sanity_check)

# Date format string for displaying datetimes in UTC.
# Example: 2013-03-21 13:00 UTC
HUMAN_READABLE_DATETIME_FORMAT = '%Y-%m-%d, %H:%M UTC'

# Date format string for displaying dates. Example: 2013-03-21
HUMAN_READABLE_DATE_FORMAT = '%Y-%m-%d'

# Time format string for displaying times. Example: 01:16:40 UTC.
HUMAN_READABLE_TIME_FORMAT = '%H:%M:%S UTC'


class ReflectiveRequestHandler(object):
    """Uses reflection to handle custom get() and post() requests.

    Use this class as a mix-in with any webapp2.RequestHandler to allow request
    dispatching to multiple get() and post() methods based on the 'action'
    parameter.

    Open your existing webapp2.RequestHandler, add this class as a mix-in.
    Define the following class variables:

        default_action = 'list'
        get_actions = ['default_action', 'edit']
        post_actions = ['save']

    Add instance methods named get_list(self), get_edit(self), post_save(self).
    These methods will now be called automatically based on the 'action'
    GET/POST parameter.
    """

    def create_xsrf_token(self, action):
        return XsrfTokenManager.create_xsrf_token(action)

    def get(self):
        """Handles GET."""
        action = self.request.get('action')
        if not action:
            action = self.default_action

        if action not in self.get_actions:
            logging.warning('Action %s is not in allowed GET actions', action)
            self.error(404)
            return

        handler = getattr(self, 'get_%s' % action)
        if not handler:
            logging.warning('Handler for get_%s not present', action)
            self.error(404)
            return

        return handler()

    def head(self):
        """Handles HEAD."""
        action = self.request.get('action')
        if not action:
            action = self.default_action

        if not hasattr(self, 'head_actions') or action not in self.head_actions:
            logging.warning('Action %s is not in allowed HEAD actions', action)
            self.error(405)
            return

        handler = getattr(self, 'head_%s' % action)
        if not handler:
            logging.warning('Handler for head_%s not present', action)
            self.error(404)
            return

        return handler()

    def post(self):
        """Handles POST."""
        action = self.request.get('action')
        if not action or action not in self.post_actions:
            logging.warning('Action %s is not in allowed POST actions', action)
            self.error(404)
            return

        handler = getattr(self, 'post_%s' % action)
        if not handler:
            logging.warning('Handler for post_%s not present', action)
            self.error(404)
            return

        # Each POST request must have valid XSRF token.
        xsrf_token = self.request.get('xsrf_token')
        if not XsrfTokenManager.is_xsrf_token_valid(xsrf_token, action):
            logging.warning("Denying post because of invalid xsrf token")
            self.error(403)
            return

        return handler()


class ApplicationHandler(webapp2.RequestHandler):
    """A handler that is aware of the application context."""

    @classmethod
    def is_absolute(cls, url):
        return bool(urlparse.urlparse(url).scheme)

    @classmethod
    def get_base_href(cls, handler):
        """Computes current course <base> href."""
        base = handler.app_context.get_slug()
        if not base.endswith('/'):
            base = '%s/' % base

        # For IE to work with the <base> tag, its href must be an absolute URL.
        if not cls.is_absolute(base):
            parts = urlparse.urlparse(handler.request.url)
            base = urlparse.urlunparse(
                (parts.scheme, parts.netloc, base, None, None, None))
        return base

    def __init__(self, *args, **kwargs):
        super(ApplicationHandler, self).__init__(*args, **kwargs)
        self.template_value = {}
    
    def mess_with_template_environ(self, environ):
        pass

    def get_template(self, template_file, additional_dirs=None):
        """Computes location of template files for the current namespace."""
        self.template_value[COURSE_INFO_KEY] = self.app_context.get_environ()
        self.template_value['is_course_admin'] = Roles.is_course_admin(
            self.app_context)
        self.template_value[
            'is_read_write_course'] = self.app_context.fs.is_read_write()
        self.template_value['is_super_admin'] = Roles.is_super_admin()
        self.template_value['ga_analytics_key'] = GOOGLE_ANALYTICS_KEY.value
        self.template_value['ga_analytics_site'] = self.request.host
        self.template_value[COURSE_BASE_KEY] = self.get_base_href(self)
        environ = self.app_context.get_template_environ(
            self.template_value[COURSE_INFO_KEY]['course']['locale'],
            additional_dirs
            )
        self.mess_with_template_environ(environ)
        return environ.get_template(template_file)

    def canonicalize_url(self, location):
        """Adds the current namespace URL prefix to the relative 'location'."""
        is_relative = (
            not self.is_absolute(location) and
            not location.startswith(self.app_context.get_slug()))
        has_slug = (
            self.app_context.get_slug() and self.app_context.get_slug() != '/')
        if is_relative and has_slug:
            location = '%s%s' % (self.app_context.get_slug(), location)
        return location

    def redirect(self, location, normalize=True):
        if normalize:
            location = self.canonicalize_url(location)
        super(ApplicationHandler, self).redirect(location)


class BaseHandler(ApplicationHandler):
    """Base handler."""

    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)
        self.course = None

    def get_course(self):
        if not self.course:
            self.course = Course(self)
        return self.course

    def find_unit_by_id(self, unit_id):
        """Gets a unit with a specific id or fails with an exception."""
        return self.get_course().find_unit_by_id(unit_id)

    def get_units(self):
        """Gets all units in the course."""
        return self.get_course().get_units()

    def get_lessons(self, unit_id):
        """Gets all lessons (in order) in the specific course unit."""
        return self.get_course().get_lessons(unit_id)

    def get_progress_tracker(self):
        """Gets the progress tracker for the course."""
        return self.get_course().get_progress_tracker()

    def get_user(self):
        """Validate user exists."""
        user = users.get_current_user()
        if not user:
            self.redirect(
                users.create_login_url(self.request.uri), normalize=False)
        else:
            return user

    def personalize_page_and_get_user(self):
        """If the user exists, add personalized fields to the navbar."""
        user = self.get_user()
        if user:
            self.template_value['email'] = user.email()
            self.template_value['logoutUrl'] = (
                users.create_logout_url(self.request.uri))

            # configure page events
            self.template_value['record_page_events'] = (
                CAN_PERSIST_PAGE_EVENTS.value)
            self.template_value['event_xsrf_token'] = (
                XsrfTokenManager.create_xsrf_token('event-post'))

        return user

    def personalize_page_and_get_enrolled(self):
        """If the user is enrolled, add personalized fields to the navbar."""
        user = self.personalize_page_and_get_user()
        if not user:
            self.redirect(
                users.create_login_url(self.request.uri), normalize=False)
            return None

        student = Student.get_enrolled_student_by_email(user.email())
        if not student:
            self.redirect('/preview')
            return None

        # Patch Student models which (for legacy reasons) do not have a user_id
        # attribute set.
        if not student.user_id:
            student.user_id = user.user_id()
            student.put()

        return student

    def assert_xsrf_token_or_fail(self, request, action):
        """Asserts the current request has proper XSRF token or fails."""
        token = request.get('xsrf_token')
        if not token or not XsrfTokenManager.is_xsrf_token_valid(token, action):
            logging.warning("Bad or missing XSRF token for %s %s (wanted action %s)",
                    request.method, request.url, action)
            self.error(403)
            return False
        return True

    def assert_participant_or_fail(self, user=None):
        if not user:
            user = self.get_user()
        if not (user and user.is_enrolled and user.is_participant):
            self.redirect('confirm?redirect=1')
            return False
        return True


    def render(self, template_file):
        """Renders a template."""
        template = self.get_template(template_file)
        self.response.out.write(template.render(self.template_value))


class BaseRESTHandler(BaseHandler):
    """Base REST handler."""

    def assert_xsrf_token_or_fail(self, token_dict, action, args_dict):
        """Asserts that current request has proper XSRF token or fails."""
        token = token_dict.get('xsrf_token')
        if not token or not XsrfTokenManager.is_xsrf_token_valid(token, action):
            transforms.send_json_response(
                self, 403,
                'Bad XSRF token. Please reload the page and try again',
                args_dict)
            return False
        return True


class PreviewHandler(BaseHandler):
    """Handler for viewing course preview."""

    def get(self):
        """Handles GET requests."""
        user = users.get_current_user()
        if not user:
            self.template_value['loginUrl'] = (
                users.create_login_url(self.request.uri))
        else:
            self.template_value['email'] = user.email()
            self.template_value['logoutUrl'] = (
                users.create_logout_url(self.request.uri))

        self.template_value['navbar'] = {'course': True}
        self.template_value['units'] = self.get_units()
        if user and Student.get_enrolled_student_by_email(user.email()):
            self.redirect('/course')
        else:
            self.render('preview.html')

"""Added by Miguel Lara"""
class FAQHandler(BaseHandler):
    """Handler for viewing course FAQ."""

    def get(self):
        """Handles GET requests."""
        user = users.get_current_user()
        if not user:
            self.template_value['loginUrl'] = (
                users.create_login_url(self.request.uri))
        else:
            self.template_value['email'] = user.email()
            self.template_value['logoutUrl'] = (
                users.create_logout_url(self.request.uri))

        self.template_value['navbar'] = {'course': True}
        self.template_value['units'] = self.get_units()
        self.render('faq.html')

class RegisterHandler(BaseHandler):
    """Handler for course registration."""

    def get(self):
        """Handles GET request."""

        user = self.personalize_page_and_get_user()
        if not user:
            self.redirect(
                users.create_login_url(self.request.uri), normalize=False)
            return

        student = Student.get_enrolled_student_by_email(user.email())
        if student:
            self.redirect('/course')
            return

        self.template_value['navbar'] = {'registration': True}
        self.template_value['register_xsrf_token'] = (
            XsrfTokenManager.create_xsrf_token('register-post'))
        self.render('register.html')

    def find_missing_fields(self, post):
        required_fields = ('name', 'location_city', 'education_level',
                'location_country', 'role')

        missing = []

        for f in required_fields:
            if not post.get(f, None):
                missing += [f]

        # Don't want to deal with the rest of the validation yet.
        if missing:
            return missing

        role_details = {
                'educator': 'grade_levels',
                'faculty': 'faculty_area',
                'administrator': 'title_and_setting',
                'researcher': 'research_area',
                'student': 'student_subject',
                'other': 'other_role',
                }

        user_role = post['role']

        if not user_role in role_details:
            missing += ['role']
        elif not post.get(role_details[user_role], None):
            missing += [role_details[user_role]]

        return missing


    def post(self):
        """Handles POST requests."""
        user = self.personalize_page_and_get_user()
        if not user:
            self.redirect(
                users.create_login_url(self.request.uri), normalize=False)
            return

        if not self.assert_xsrf_token_or_fail(self.request, 'register-post'):
            return

        can_register = self.app_context.get_environ(
            )['reg_form']['can_register']
        if not can_register:
            self.template_value['course_status'] = 'full'
        else:
            missing = self.find_missing_fields(self.request.POST)
            if missing:
                self.template_value['navbar'] = {'registration': True}
                self.template_value['content'] = '''
                <div class="gcb-col-11 gcb-aside">
                <h2>Something is missing...</h2>
                <p>You didn't fill out all the required fields in the registration form.
                Please use your browser's BACK button, and complete the form before
                submitting.</p>

                <p>Missing: {0}</p>

                <p>Thanks!</p>
                </div>
                '''.format(", ".join(missing))
                self.render('bare.html')
                return

            # We accept the form.  Now populate the student model:

            # create new or re-enroll old student
            student = Student.get_by_email(user.email())
            if not student:
                student = Student(key_name=user.email())
                student.user_id = user.user_id()

            student_by_uid = Student.get_student_by_user_id(user.user_id())
            is_valid_student = (student_by_uid is None or
                                student_by_uid.user_id == student.user_id)
            assert is_valid_student, (
                'Student\'s email and user id do not match.')

            student.user_id = user.user_id()
            student.is_enrolled = True

            string_fields = ('name', 'location_city',
                    'location_state', 'location_country',
                    'education_level', 'role',
                    'other_role')

            for field in string_fields:
                setattr(student, field, self.request.POST.get(field, None))

            string_list_fields = ('grade_levels', 'title_and_setting',
                    'research_area', 'faculty_area', 'student_subject')

            for field in string_list_fields:
                raw = self.request.POST.get(field, '')
                if len(raw) > 0:
                    values = [s.strip() for s in raw.split(',')]
                    setattr(student, field, values)

            student.put()

            # now that we're in full registration, don't subscribe to pre-reg any more
            #mailchimp.subscribe('pre-reg', user.email(), student.name)

            self.redirect('confirm')
            return

        # Render registration confirmation page
        self.template_value['navbar'] = {'registration': True}
        self.render('confirmation.html')



class ForumHandler(BaseHandler):
    """Handler for forum page."""

    def get(self):
        """Handles GET requests."""
        if not self.personalize_page_and_get_enrolled():
            return

        self.template_value['navbar'] = {'forum': True}
        self.render('forum.html')


class StudentProfileHandler(BaseHandler):
    """Handles the click to 'My Profile' link in the nav bar."""

    def get(self):
        """Handles GET requests."""
        student = self.personalize_page_and_get_enrolled()
        if not student:
            return

        course = self.get_course()

        self.template_value['navbar'] = {'myprofile': True}
        self.template_value['student'] = student
        self.template_value['assertion_link'] = lambda a: self.request.host_url + modules.badges.util.url_for_key(a.key())
        self.template_value['date_enrolled'] = student.enrolled_on.strftime(
            HUMAN_READABLE_DATE_FORMAT)
        self.template_value['score_list'] = course.get_all_scores(student)
        self.template_value['overall_score'] = course.get_overall_score(student)
        self.template_value['part_reports'] = [PartReport.on(student, course, p) for p in (1,2,3)]
        self.template_value['expert_report'] = ExpertBadgeReport.on(student, course)
        self.template_value['student_edit_xsrf_token'] = (
            XsrfTokenManager.create_xsrf_token('student-edit'))
        self.render('student_profile.html')


class StudentEditBadgeNameHandler(BaseHandler):
    """Handles edits to student records by students."""

    def post(self):
        """Handles POST requests."""
        student = self.personalize_page_and_get_enrolled()
        if not student:
            return

        if not self.assert_xsrf_token_or_fail(self.request, 'student-edit'):
            return

        Student.set_badge_name_for_current(self.request.get('badgename'))

        self.redirect('/student/home')

class StudentEditStudentHandler(BaseHandler):
    """Handles edits to student records by students."""

    def post(self):
        """Handles POST requests."""
        student = self.personalize_page_and_get_enrolled()
        if not student:
            return

        if not self.assert_xsrf_token_or_fail(self.request, 'student-edit'):
            return

        Student.rename_current(self.request.get('name'))

        self.redirect('/student/home')


class StudentUnenrollHandler(BaseHandler):
    """Handler for students to unenroll themselves."""

    class SurveyForm(wtf.Form):
        how_found_out = wtf.RadioField(
                'How did you initially find out about the Assessment BOOC?',
                choices=[
                    ('facebook', 'Facebook'),
                    ('twitter', 'Twitter'),
                    ('google-ads', 'Google Ads'),
                    ('assess-blog', 'Remediating Assessment Blog'),
                    ('word-of-mouth', 'Word of Mouth (please elaborate below...'),
                    ('print', 'Print Advertisements'),
                    ('other', 'Other (please elaborate below...)'),
                    ],
                validators=[wtf.validators.Required()])
        how_found_out_other = wtf.TextField(
                '''If you selected "Word of Mouth," whom did you hear from?<br>
                If you selected "Other," how did you hear about the course?''',
                validators=[wtf.validators.Optional()])
        difficulty = wtf.TextAreaField(
                'Did the course meet your expectations in terms of the difficulty of the tasks?',
                validators=[wtf.validators.Required('Please give us at least a word...')])
        communication = wtf.TextAreaField(
                'Did you feel that course expectations were well-communicated?',
                validators=[wtf.validators.Required('Please give us at least a word...')])
        better_communication = wtf.TextAreaField(
                'What might we have done differently to communicate the course expectations?',
                validators=[wtf.validators.Required('Please give us at least a word...')])
        other_comments = wtf.TextAreaField(
                'Do you have any other comments or suggestions?',
                validators=[wtf.validators.Optional()])

    def get(self):
        """Handles GET requests."""
        student = self.personalize_page_and_get_enrolled()
        if not student:
            return

        self.render_form(student, self.SurveyForm())

    def render_form(self, student, form):
        self.template_value['student'] = student
        self.template_value['form'] = form
        self.template_value['navbar'] = {'registration': True}
        self.template_value['student_unenroll_xsrf_token'] = (
            XsrfTokenManager.create_xsrf_token('student-unenroll'))
        self.render('unenroll_confirmation_check.html')

    def post(self):
        """Handles POST requests."""
        student = self.personalize_page_and_get_enrolled()
        if not student:
            return

        if not self.assert_xsrf_token_or_fail(self.request, 'student-unenroll'):
            return

        form = self.SurveyForm(self.request.POST)
        if not form.validate():
            self.render_form(student, form)
            return

        info = {
                'email': student.key().name(),
                'wikis_posted': student.wikis_posted,
                }
        info.update(form.data)

        # form is good
        EventEntity.record(
                'unenrolled',
                users.get_current_user(),
                transforms.dumps(info))

        mail.send_mail('booc.class@gmail.com', 'booc.class@gmail.com',
                'User %s unenrolled' % info['email'],
                'Their data:\n%s' % transforms.dumps(info, indent=2))

        Student.set_enrollment_status_for_current(False)
        mailchimp.unsubscribe('pre-reg', student.key().name())
        mailchimp.unsubscribe('confirmed', student.key().name())
        mailchimp.unsubscribe('for-credit', student.key().name())
        mailchimp.subscribe('unenrolled', student.key().name(), student.name)

        self.template_value['navbar'] = {'registration': True}
        self.render('unenroll_confirmation.html')


class XsrfTokenManager(object):
    """Provides XSRF protection by managing action/user tokens in memcache."""

    # Max age of the token (4 hours).
    XSRF_TOKEN_AGE_SECS = 60 * 60 * 12

    # Token delimiters.
    DELIMITER_PRIVATE = ':'
    DELIMITER_PUBLIC = '/'

    # Default nickname to use if a user does not have a nickname,
    USER_ID_DEFAULT = 'default'

    @classmethod
    def init_xsrf_secret_if_none(cls):
        """Verifies that non-default XSRF secret exists; creates one if not."""

        # Any non-default value is fine.
        if XSRF_SECRET.value and XSRF_SECRET.value != XSRF_SECRET.default_value:
            return

        # All property manipulations must run in the default namespace.
        old_namespace = namespace_manager.get_namespace()
        try:
            namespace_manager.set_namespace(
                appengine_config.DEFAULT_NAMESPACE_NAME)

            # Look in the datastore directly.
            entity = ConfigPropertyEntity.get_by_key_name(XSRF_SECRET.name)
            if not entity:
                entity = ConfigPropertyEntity(key_name=XSRF_SECRET.name)

            # Any non-default non-None value is fine.
            if (entity.value and not entity.is_draft and
                (str(entity.value) != str(XSRF_SECRET.default_value))):
                return

            # Initialize to random value.
            entity.value = base64.urlsafe_b64encode(
                os.urandom(XSRF_SECRET_LENGTH))
            entity.is_draft = False
            entity.put()
        finally:
            namespace_manager.set_namespace(old_namespace)

    @classmethod
    def _create_token(cls, action_id, issued_on):
        """Creates a string representation (digest) of a token."""
        cls.init_xsrf_secret_if_none()

        # We have decided to use transient tokens stored in memcache to reduce
        # datastore costs. The token has 4 parts: hash of the actor user id,
        # hash of the action, hash of the time issued and the plain text of time
        # issued.

        # Lookup user id.
        user = users.get_current_user()
        if user:
            user_id = user.user_id()
        else:
            user_id = cls.USER_ID_DEFAULT

        # Round time to seconds.
        issued_on = long(issued_on)

        digester = hmac.new(str(XSRF_SECRET.value))
        digester.update(str(user_id))
        digester.update(cls.DELIMITER_PRIVATE)
        digester.update(str(action_id))
        digester.update(cls.DELIMITER_PRIVATE)
        digester.update(str(issued_on))

        digest = digester.digest()
        token = '%s%s%s' % (
            issued_on, cls.DELIMITER_PUBLIC, base64.urlsafe_b64encode(digest))

        return token

    @classmethod
    def create_xsrf_token(cls, action):
        return cls._create_token(action, time.time())

    @classmethod
    def is_xsrf_token_valid(cls, token, action):
        """Validate a given XSRF token by retrieving it from memcache."""
        try:
            parts = token.split(cls.DELIMITER_PUBLIC)
            if len(parts) != 2:
                logging.warning("Malformed XSRF token")
                return False

            issued_on = long(parts[0])
            age = time.time() - issued_on
            if age > cls.XSRF_TOKEN_AGE_SECS:
                logging.warning("XSRF token too old (%s)", str(age))
                return False

            authentic_token = cls._create_token(action, issued_on)
            if authentic_token == token:
                return True

            logging.warning("XSRF token doesn't match")
            return False
        except Exception:  # pylint: disable-msg=broad-except
            return False

