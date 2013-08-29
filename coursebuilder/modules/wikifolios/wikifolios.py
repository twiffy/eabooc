"""
Wikifolios module for Google Course Builder
"""

from models import custom_modules, transforms
from models.config import ConfigProperty
from models.models import Student, EventEntity, MemcacheManager
from models.roles import Roles
from common import ckeditor, prefetch
import bleach
import webapp2
import humanize
from controllers.utils import BaseHandler, ReflectiveRequestHandler
from modules.wikifolios.wiki_models import WikiPage, WikiComment, Annotation
from google.appengine.api import users, mail
import itertools, collections
import textwrap
import filters
import logging
import functools
import urllib
import wtforms as wtf
from jinja2 import Markup

NO_OBJECT = {}

STUDENTS_CAN_DO_ASSIGNMENTS = ConfigProperty(
        'students_can_do_assignments', bool,
        """Whether to allow students to create and edit pages on their
        wikifolios, other than their profiles.""",
        True)

def get_student_by_wiki_id(wiki_id):
    return Student.get_enrolled_student_by_wiki_id(wiki_id)

def student_profile_link(wiki_id):
    return "wikiprofile?" + urllib.urlencode({'student': wiki_id})

ALLOWED_TAGS = (
        # bleach.ALLOWED_TAGS:
        'a', 'abbr', 'acronym', 'b',
        'blockquote', 'code', 'em', 'i',
        'li', 'ol', 'strong', 'ul',
        # more:
        'p', 'strike', 'img', 'table',
        'thead', 'tr', 'td', 'th',
        'hr', 'caption', 'summary',
        'tbody',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'div', 'big', 'small', 'tt', 'pre',
        )
ALLOWED_ATTRIBUTES = {
        # bleach.ALLOWED_ATTRIBUTES:
        'a': ['href', 'title'],
        'abbr': ['title'],
        'acronym': ['title'],
        # more:
        'img': ['src', 'alt', 'title'],
        'table': ['border', 'cellpadding', 'cellspacing', 'style',
            'bordercolor'],
        'th': ['scope'],
        'p': ['style'],
        'div': ['style'],
        }
ALLOWED_STYLES = (
        # (Bleach's default is no styles allowed)
        'color', 'width', 'height', 'background-color',
        'border-collapse', 'padding', 'border',
        'font-style',
        )

def bleach_entry(html):
    cleaned = bleach.clean(html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            styles=ALLOWED_STYLES,
            )
    return bleach.linkify(cleaned)

COMMENT_TAGS = (
        'a', 'b',
        'blockquote', 'i',
        'li', 'ol', 'ul',
        'p', 'tt',
        )
COMMENT_ATTRIBUTES = {
        # bleach.ALLOWED_ATTRIBUTES:
        'a': ['href', 'title'],
        }
COMMENT_STYLES = ()

def bleach_comment(html):
    return bleach.clean(html,
            tags=COMMENT_TAGS,
            attributes=COMMENT_ATTRIBUTES,
            styles=COMMENT_STYLES,
            )

class WikiBaseHandler(BaseHandler):
    # I don't like how leaky this is, always having to check for the None return.
    def personalize_page_and_get_wiki_user(self):
        user = self.personalize_page_and_get_enrolled()
        self.template_value['navbar'] = {'wiki': True}
        self.template_value['content'] = ''
        self.template_value['student_link'] = filters.student_link
        self.template_value['humanize'] = humanize
        if hasattr(self, 'create_xsrf_token'):
            # TODO: refactor to split more complicated pages out from the profile list handler
            self.template_value['create_xsrf_token'] = self.create_xsrf_token
        self.template_value['can_do_assignments'] = STUDENTS_CAN_DO_ASSIGNMENTS.value
        self.template_value['user_can_edit_comment'] = functools.partial(
                self._user_can_edit_comment, user)
        if not user or not self.assert_participant_or_fail(user):
            return
        return user

    def show_notifications(self, current_student):
        self.template_value['notifications'] = current_student.read_notifications()

    def _editor_role(self, query, current_student, template=True):
        if not (query and current_student):
            return None
        if current_student:
            assert current_student.key().name() == users.get_current_user().email()
        is_author = (current_student
                and current_student.wiki_id == query['student']
                and current_student.is_enrolled)
        role = None
        if is_author:
            role = 'author'
        elif Roles.is_course_admin(self.app_context):
            role = 'admin'
        if template:
            self.template_value['editor_role'] = role
            if role != 'author':
                self.template_value['navbar'] = {'participants': True}
        return role

    def assert_editor_role(self, *args, **kwargs):
        role = self._editor_role(*args, **kwargs)
        if not role:
            self.abort(403, "You cannot edit this page.")
        return role

    def _can_view(self, query, current_student):
        if current_student:
            assert current_student.key().name() == users.get_current_user().email()
        is_enrolled = (current_student and current_student.is_enrolled)
        return is_enrolled or Roles.is_course_admin(self.app_context)

    def _user_can_edit_comment(self, user, comment):
        # would be great to use the same code as _editor_role above...
        author_id = str(WikiComment.author.get_value_for_datastore(comment))
        return str(user.key()) == author_id or Roles.is_course_admin(self.app_context)

    def _can_comment(self, query, current_student):
        return self._can_view(query, current_student)

    def _create_action_url(self, query, action="view"):
        params = dict(query)
        params.update({
                'action': action,
                })
        return '?'.join((
                self.request.path,
                urllib.urlencode(params)))

    def post_comment(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)

        if not query:
            self.abort(404)

        if not self._can_comment(query, user):
            logging.warning("Attempt to comment illegally")
            self.abort(403, "You are not allowed to comment on this page.")

        page = self._find_page(query)
        if not page:
            self.abort(404)

        # TODO: use wtforms for comments
        comment = WikiComment(
                author=user,
                topic=page,
                text=bleach_comment(self.request.get('text', '')))
        comment.put()

        EventEntity.record(
                'wiki-comment', users.get_current_user(), transforms.dumps({
                    'page-author': page.author.key().name(),
                    'page': str(page.key()),
                    'unit': page.unit,
                    'commenter': user.key().name(),
                    'text': comment.text,
                    'unbleached-text': self.request.get('text', ''),
                    }))

        if query['student'] != user.wiki_id:
            note = Markup('<a href="%(url)s"><b>%(commenter)s</b> commented on %(what)s</a>')
            page.author.notify(unicode(note % {
                'url': self._create_action_url(query, 'view'),
                'commenter': user.name,
                'what': self.describe_query(query, page.author),
                }))

        self.redirect(self._create_action_url(query, 'view'))

    def post_flag(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)

        if not query:
            self.abort(404)

        if not self._can_view(query, user):
            logging.warning("Attempt to flag a page they can't see????")
            self.abort(403, "You are not allowed to do that.")

        page = self._find_page(query)
        if not page:
            self.abort(404)

        raw_reason = self.request.get('reason', '')
        reason = bleach_comment(raw_reason[:2000]) # limit size, de-fang

        Annotation.flag(
                page,
                user,
                reason)

        url = self.request.host_url + self._create_action_url(query, 'view')
        flagger_id = '%s <%s>' % (user.name, user.key().name())
        mail.send_mail_to_admins('BOOC Admin <booc.class@gmail.com>',
                'Inappropriate content reported',
                textwrap.dedent('''\
                The user %(flagger_id)s reported inappropriate content on this page:

                %(url)s

                Their comment was:

                %(reason)s
                ''' % {
                    'flagger_id': flagger_id,
                    'url': url,
                    'reason': reason,
                    }),
                reply_to=flagger_id)

        self.template_value['content'] = '''
            <div class="gcb-aside">
            <h1>Thank you for your report.</h1>
            It has been sent to the
            course administrators for review.
            </div>
            '''
        self.render('bare.html')

class WikiCommentHandler(WikiBaseHandler, ReflectiveRequestHandler):
    default_action = 'edit'
    get_actions = ['edit', 'delete']
    post_actions = ['save', 'delete']

    class _NavForm(wtf.Form):
        comment_id = wtf.IntegerField('Comment ID', [wtf.validators.Required()])

    def _find_comment(self):
        form = self._NavForm(self.request.GET)
        if not form.validate():
            self.abort(404)

        comment = WikiComment.get_by_id(form.comment_id.data)
        if not comment:
            self.abort(404, "The requested comment could not be found.")

        return comment

    def get_edit(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        comment = self._find_comment()
        if comment.is_deleted:
            self.template_value['content'] = 'You cannot edit a deleted comment'
            self.render('bare.html')
            return

        query = {
                'student': comment.author.wiki_id,
                'comment_id': comment.key().id(),
                }
        self.assert_editor_role(query, user)

        self.template_value['ckeditor_allowed_content'] = (
                ckeditor.allowed_content(ALLOWED_TAGS,
                    ALLOWED_ATTRIBUTES, ALLOWED_STYLES))

        self.template_value['author_name'] = comment.author.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])
        self.template_value['content'] = comment.text
        self.template_value['action_url'] = functools.partial(
                self._create_action_url, query)
        self.render("wf_comment_edit.html")

    def post_save(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        comment = self._find_comment()
        if comment.is_deleted:
            self.template_value['content'] = 'You cannot edit a deleted comment'
            self.render('bare.html')
            return

        query = {
                'student': comment.author.wiki_id,
                'comment_id': comment.key().id(),
                }
        self.assert_editor_role(query, user)

        old_text = comment.text
        comment.text = bleach_comment(self.request.get('text', ''))
        comment.is_edited = True
        comment.editor = user
        comment.put()

        EventEntity.record(
                'wiki-comment-edit', users.get_current_user(), transforms.dumps({
                    'comment-author': comment.author.key().name(),
                    'comment': str(comment.key()),
                    'editor': user.key().name(),
                    'text': comment.text,
                    'old-text': old_text,
                    'unbleached-text': self.request.get('text', ''),
                    }))

        self.redirect(comment.topic.link)

    def get_delete(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        comment = self._find_comment()

        query = {
                'student': comment.author.wiki_id,
                'comment_id': comment.key().id(),
                }
        self.assert_editor_role(query, user)

        self.template_value['author_name'] = comment.author.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])
        self.template_value['content'] = comment.text
        self.template_value['action_url'] = functools.partial(
                self._create_action_url, query)
        self.render("wf_comment_delete.html")

    def post_delete(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        comment = self._find_comment()

        query = {
                'student': comment.author.wiki_id,
                'comment_id': comment.key().id(),
                }
        self.assert_editor_role(query, user)

        EventEntity.record(
                'wiki-comment-delete', users.get_current_user(), transforms.dumps({
                    'comment-author': comment.author.key().name(),
                    'comment': str(comment.key()),
                    'editor': user.key().name(),
                    'text': comment.text,
                    }))

        comment.is_deleted = True
        comment.is_edited = True
        comment.editor = user
        comment.put()
        self.redirect(comment.topic.link)


class WikiPageHandler(WikiBaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = ["view", "edit"]
    post_actions = ["save", "comment", "endorse", "flag", "exemplary"]

    class _NavForm(wtf.Form):
        unit = wtf.IntegerField('Unit number', [
            wtf.validators.NumberRange(min=1, max=100),
            ])
        student = wtf.IntegerField('Student id', [
            wtf.validators.Optional(),
            wtf.validators.NumberRange(min=1, max=100000000000),
            ])

    def describe_query(self, query, user):
        "Describes the query to a particular user"
        if query['student'] == user.wiki_id:
            whose = "your "
        else:
            whose = Markup("<b>%s</b>'s ") % get_student_by_wiki_id(query['student']).name

        what = Markup("unit %s wikifolio page") % query['unit']
        return whose + what


    def _get_query(self, user):
        form = self._NavForm(self.request.params)
        data = None
        if form.validate():
            data = form.data
        else:
            # TODO maybe log why it's not good
            self.template_value['content'] = 'Sorry, that page was not found.'
            self.error(403)
            data = None

        if data and not data['student'] and user:
            data['student'] = user.wiki_id

        self.template_value['action_url'] = functools.partial(
                self._create_action_url, data)
        return data

    def _find_page(self, query, create=False):
        logging.info(query)
        assert query
        # TODO don't have to do this query if it's your own page,
        # optimize this.  Also, cache.
        # TODO maybe store the wiki_id of the student in the Page,
        # and look up by that, so we don't fetch the Student
        # model twice (once by wiki id, once as a reference in
        # the page)
        student_model = get_student_by_wiki_id(query['student'])
        if not student_model:
            return None

        key = WikiPage.get_key(student_model, query['unit'])
        if not key:
            # Not only is there no page,
            # but the request is invalid too.
            return None

        page = WikiPage.get(key)
        if (not page) and create:
            page = WikiPage(key=key)

        return page


    def get_view(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)

        if not query:
            self.abort(404)
        elif not self._can_view(query, user):
            # They may have already bounced off the login page
            # from personalize_page_etc above
            self.abort(403)
        editor_role = self._editor_role(query, user)
        self.template_value['unit'] = list([u for u in self.get_units() if u.unit_id == unicode(query['unit'])])[0]
        self.template_value['author'] = get_student_by_wiki_id(query['student'])

        page = self._find_page(query)
        if page:
            content = page.text

            self.show_notifications(user)
            self.template_value['comments'] = prefetch.prefetch_refprops(
                    page.comments.order("added_time").fetch(limit=1000),
                    WikiComment.author)

            if self._can_comment(query, user):
                self.template_value['can_comment'] = True
                self.template_value['ckeditor_comment_content'] = (
                        ckeditor.allowed_content(COMMENT_TAGS,
                            COMMENT_ATTRIBUTES, COMMENT_STYLES))

            self.template_value['endorsements'] = prefetch.prefetch_refprops(
                    Annotation.endorsements(page), Annotation.who)

            self.template_value['exemplaries'] = prefetch.prefetch_refprops(
                    Annotation.exemplaries(page), Annotation.who)

            if query['student'] == user.wiki_id:
                self.template_value['is_author'] = True
                self.template_value['endorsement_view'] = 'author'
                self.template_value['exemplary_view'] = 'author'
            else:
                if Annotation.endorsements(page, user).count(limit=1) > 0:
                    self.template_value['endorsement_view'] = 'has_endorsed'
                else:
                    self.template_value['endorsement_view'] = 'can_endorse'

                if Annotation.exemplaries(page, user).count(limit=1) > 0:
                    self.template_value['exemplary_view'] = 'has_exemplaried'
                else:
                    self.template_value['exemplary_view'] = 'can_exemplary'
        else:
            content = "The page you requested could not be found."
            self.error(404)

        self.template_value['content'] = content
        self.render("wf_page.html")

    def post_exemplary(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)
        if not query:
            self.abort(404)
        content = ''

        if not self._can_view(query, user):
            self.abort(403)
        elif user.wiki_id == query['student']:
            logging.warning("Attempt to mark own page as exemplary")
            self.abort(403, "You are not allowed to mark your own page exemplary.")

        page = self._find_page(query)
        if Annotation.exemplaries(page, user).count(limit=1) > 0:
            logging.warning("Attempt to mark complete multiple times.")
            self.abort(403, "You've already marked this page exemplary.")

        Annotation.exemplary(page, user,
                reason=bleach_comment(self.request.get('comment')))

        self.redirect(self._create_action_url(query, 'view'))

    def post_endorse(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)
        if not query:
            self.abort(404)
        content = ''

        if not self._can_view(query, user):
            self.abort(403)
        elif user.wiki_id == query['student']:
            logging.warning("Attempt to mark own page as complete")
            self.abort(403, "You are not allowed to mark your own page complete.")

        page = self._find_page(query)
        if Annotation.endorsements(page, user).count(limit=1) > 0:
            logging.warning("Attempt to mark complete multiple times.")
            self.abort(403, "You've already marked this page complete.")

        Annotation.endorse(page, user, 'all_done' in self.request.POST)
        self.redirect(self._create_action_url(query, 'view'))


    def get_edit(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)
        self.template_value['ckeditor_allowed_content'] = (
                ckeditor.allowed_content(ALLOWED_TAGS,
                    ALLOWED_ATTRIBUTES, ALLOWED_STYLES))

        if not query:
            self.abort(404)

        self.assert_editor_role(query, user)

        # We call with create=True to eliminate a conditional on how
        # to set the author_name later.  But we don't .put() it.
        page = self._find_page(query, create=True)
        content = page.text or ''

        self.template_value['author_name'] = page.author.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])
        self.template_value['content'] = content
        self.render("wf_edit.html")

    def get_unit(self, unit_id):
        # TODO find_unit_by_id??
        unit_id = unicode(unit_id) # harrumph
        units = self.get_units()
        for unit in units:
            if unit.unit_id == unit_id:
                return unit

    def post_save(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)

        self.assert_editor_role(query, user)
        if not STUDENTS_CAN_DO_ASSIGNMENTS.value:
            logging.warning("Assignments not yet open (STUDENTS_CAN_DO_ASSIGNMENTS is false)")
            content = "Assignments are not yet available."
            self.error(403)
            self.render("bare.html")
            return
        page = self._find_page(query, create=True)

        old_text = page.text
        page.text = bleach_entry(self.request.get('text', ''))
        page.unit = query['unit']
        page.title = self.get_unit(query['unit']).title

        page.put()
        EventEntity.record(
                'edit-wiki-page', users.get_current_user(), transforms.dumps({
                    'page-author': page.author.key().name(),
                    'page-editor': user.key().name(),
                    'unit': page.unit,
                    'before': old_text,
                    'after': page.text,
                    }))
        self.redirect(self._create_action_url(query, 'view'))


class WikiProfileListHandler(WikiBaseHandler):
    group_names = {
                'administrator': 'Administrators',
                'educator': 'Educators (K-12)',
                'faculty': 'Faculty (Post-secondary)',
                'researcher': 'Researchers',
                'student': 'Students',
                'other': 'Other',
                }
    allowed_groups = frozenset(('role',))

    def group_name(self, db_val):
        return self.group_names.get(db_val, None) or db_val.title()

    def get(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        self.template_value['navbar'] = {'participants': True}
        self.template_value['group_name'] = self.group_name

        group_by = self.request.get('group', None)
        logging.debug(repr(group_by))
        if group_by not in self.allowed_groups:
            logging.debug('Not accepting requested grouping %s', group_by)
            group_by = None

        self.template_value['group_by'] = group_by

        projection = ['wiki_id', 'name']

        # will need to cache this somehow.
        student_list = Student.all()
        student_list.filter('is_enrolled =', True)
        student_list.filter('is_participant =', True)
        if group_by:
            student_list.order(group_by)
            projection.append(group_by)
        student_list.order('name')

        # our course is capped at 500 students, so...
        FETCH_LIMIT=600

        all_students = student_list.run(
                limit=FETCH_LIMIT,
                projection=projection,
                )
        if group_by:
            lazy_groups = itertools.groupby(all_students,
                    lambda student: getattr(student, group_by))
            self.template_value['groups'] = lazy_groups
        else:
            self.template_value['groups'] = [ ('All Students', all_students) ]


        self.render("wf_list.html")


class WikiProfileHandler(WikiBaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = [
            "view",
            "edit",
            ]
    post_actions = [
            "save",
            "comment",
            "flag",
            ]

    class _NavForm(wtf.Form):
        student = wtf.IntegerField('Student id', [
            wtf.validators.Optional(),
            wtf.validators.NumberRange(min=1, max=100000000000),
            ])

    def _get_query(self, unused_user=None):
        # TODO: maybe do redirects to ?student= from here?
        form = self._NavForm(self.request.params)
        if form.validate():
            self.template_value['action_url'] = functools.partial(
                    self._create_action_url, form.data)
            return form.data
        else:
            self.abort(404, 'Sorry, there is no such student.')

    def _find_page(self, query, create=False):
        logging.info(query)
        assert query
        # TODO don't have to do this query if it's your own page,
        # optimize this.  Also, cache.
        # TODO maybe store the wiki_id of the student in the Page,
        # and look up by that, so we don't fetch the Student
        # model twice (once by wiki id, once as a reference in
        # the page)
        student_model = get_student_by_wiki_id(query['student'])
        if not student_model:
            return None

        key = WikiPage.get_key(student_model, unit=None)
        if not key:
            # Not only is there no page,
            # but the request is invalid too.
            return None

        page = WikiPage.get(key)
        if (not page) and create:
            page = WikiPage(key=key)

        return page

    def get_view(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query()
        if not query or not query['student']:
            self.abort(302, location="wikiprofile?" + urllib.urlencode({
                'student': user.wiki_id}))

        if self.request.GET.get('confirm', False):
            self.template_value['alert'] = '''<b>Congratulations!</b> You are
                officially registered. Welcome to the course.  Have a look around!'''

        profile_page = self._find_page(query, create=True)
        if not profile_page:
            # e.g. there is no student by that ID.
            self.abort(404)
        if not profile_page.text:
            # The profile is brand new or is blank
            self.template_value['content'] = "This user has not created a profile yet."
        else:
            self.template_value['content'] = profile_page.text

        self.template_value['author_name'] = profile_page.author.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])

        editor_role = self._editor_role(query, user)

        units = self.get_units()
        pages = WikiPage.query_by_student(profile_page.author).run(limit=100)
        units_with_pages = set([ unicode(p.unit) for p in pages ])
        for unit in units:
            if unit.unit_id in units_with_pages:
                unit._wiki_exists = True
            unit._wiki_link = "wiki?" + urllib.urlencode({
                'student': profile_page.author.wiki_id,
                'action': 'view',
                'unit': unit.unit_id,
                })

        self.template_value['units'] = units

        self.template_value['endorsements'] = profile_page.author.own_annotations.filter('why IN', ['endorse', 'exemplary']).run(limit=10)

        self.show_notifications(user)
        self.template_value['comments'] = prefetch.prefetch_refprops(
                profile_page.comments.order("added_time").fetch(limit=1000),
                WikiComment.author)

        if self._can_comment(query, user):
            self.template_value['can_comment'] = True
            self.template_value['ckeditor_comment_content'] = (
                    ckeditor.allowed_content(COMMENT_TAGS,
                        COMMENT_ATTRIBUTES, COMMENT_STYLES))

        self.render("wf_profile.html")

    def get_edit(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query()
        if not query['student']:
            self.redirect("wikiprofile?" + urllib.urlencode({
                'student': user.wiki_id}))
            return

        self.assert_editor_role(query, user)

        self.template_value['ckeditor_allowed_content'] = (
                ckeditor.allowed_content(ALLOWED_TAGS,
                    ALLOWED_ATTRIBUTES, ALLOWED_STYLES))


        profile_page = self._find_page(query, create=True)
        assert profile_page
        student_model = profile_page.author

        self.template_value['author_name'] = student_model.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])

        self.template_value['content'] = profile_page.text

        self.render("wf_profile_edit.html")

    def post_save(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query()
        if not query:
            self.abort(404)

        self.assert_editor_role(query, user)

        page = self._find_page(query, create=True)

        old_text = page.text
        page.text = bleach_entry(self.request.get('text', ''))

        page.put()
        EventEntity.record(
                'edit-wiki-profile', users.get_current_user(), transforms.dumps({
                    'page-author': page.author.key().name(),
                    'page-editor': user.key().name(),
                    'before': old_text,
                    'after': page.text,
                    }))
        self.redirect(self._create_action_url(query, 'view'))
        return

    def describe_query(self, query, user):
        "Describes the query to a particular user"
        if query['student'] == user.wiki_id:
            whose = "your "
        else:
            whose = Markup("<b>%s</b>'s ") % get_student_by_wiki_id(query['student']).name

        what = Markup("profile page")
        return whose + what

module = None

def register_module():
    global module

    handlers = [
            ('/wiki', WikiPageHandler),
            ('/wikicomment', WikiCommentHandler),
            ('/wikiprofile', WikiProfileHandler),
            ('/participants', WikiProfileListHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Wikifolios", "Wikifolio pages",
            [], handlers)

    return module

