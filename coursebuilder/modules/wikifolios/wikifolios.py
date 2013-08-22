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
from controllers.utils import BaseHandler, ReflectiveRequestHandler
from modules.wikifolios.wiki_models import WikiPage, WikiComment, Annotation
from google.appengine.api import users
import filters
import logging
import urllib
import wtforms as wtf

NO_OBJECT = {}

STUDENTS_CAN_DO_ASSIGNMENTS = ConfigProperty(
        'students_can_do_assignments', bool,
        """Whether to allow students to create and edit pages on their
        wikifolios, other than their profiles.""",
        True)

# Some folks go all the way from e.g. email->rendered link in the cache
# Here's just the wiki_id->author object
def get_student_by_wiki_id(wiki_id):
    memcache_key = 'entity:student-by-wiki-id:%s' % wiki_id

    student = MemcacheManager.get(memcache_key)
    if NO_OBJECT == student:
        return None
    if not student:
        student = (Student.all()
            .filter("wiki_id =", wiki_id)
            .get())
        if student:
            MemcacheManager.set(memcache_key, student)
        else:
            MemcacheManager.set(memcache_key, NO_OBJECT)
    return student

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
        self.template_value['author_link'] = filters.author_link
        self.template_value['can_do_assignments'] = STUDENTS_CAN_DO_ASSIGNMENTS.value
        if not user or not self.assert_participant_or_fail(user):
            return
        return user

    def _editor_role(self, query, current_student):
        if current_student:
            assert current_student.key().name() == users.get_current_user().email()
        is_author = (current_student
                and current_student.wiki_id == query['student']
                and current_student.is_enrolled)
        if is_author:
            return 'author'
        elif Roles.is_course_admin(self.app_context):
            return 'admin'
        return None

    def _create_action_url(self, query, action="view"):
        params = dict(query)
        params.update({
                'action': action,
                })
        return '?'.join((
                self.request.path,
                urllib.urlencode(params)))

class WikiPageHandler(WikiBaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = ["view", "edit"]
    post_actions = ["save", "comment", "endorse"]

    class _NavForm(wtf.Form):
        unit = wtf.IntegerField('Unit number', [
            wtf.validators.NumberRange(min=1, max=100),
            ])
        student = wtf.IntegerField('Student id', [
            wtf.validators.Optional(),
            wtf.validators.NumberRange(min=1, max=100000000000),
            ])


    def _get_query(self, user):
        form = self._NavForm(self.request.params)
        data = None
        if form.validate():
            data = form.data
        else:
            # TODO maybe log why it's not good
            data = None

        if data and not data['student'] and user:
            data['student'] = user.wiki_id

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

    def _can_view(self, query, current_student):
        if current_student:
            assert current_student.key().name() == users.get_current_user().email()
        is_enrolled = (current_student and current_student.is_enrolled)
        return is_enrolled or Roles.is_course_admin(self.app_context)


    def _can_comment(self, query, current_student):
        return self._can_view(query, current_student)

    def get_view(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)
        self.template_value['navbar'] = {'wiki': True}
        self.template_value['content'] = ''
        self.template_value['view_link'] = self._create_action_url(query, 'view')

        if not query:
            logging.info("404: query is not legit.")
            content = "The page you requested could not be found."
            self.error(404)
            # fall through
        elif not self._can_view(query, user):
            # They may have already bounced off the login page
            # from personalize_page_etc above
            content = "Sorry, you can't see this page."
            self.error(403)
            # fall through
        else:
            editor_role = self._editor_role(query, user)
            self.template_value['editor_role'] = editor_role
            if editor_role != 'author':
                self.template_value['navbar'] = {'participants': True}
            self.template_value['edit_url'] = self._create_action_url(query, 'edit')
            self.template_value['unit'] = list([u for u in self.get_units() if u.unit_id == unicode(query['unit'])])[0]

            page = self._find_page(query)
            self.template_value['author'] = get_student_by_wiki_id(query['student'])
            if page:
                content = page.text
                self.template_value['comments'] = prefetch.prefetch_refprops(
                        page.comments.order("added_time").fetch(limit=1000),
                        WikiComment.author)

                if self._can_comment(query, user):
                    self.template_value['can_comment'] = True
                    self.template_value['ckeditor_comment_content'] = (
                            ckeditor.allowed_content(COMMENT_TAGS,
                                COMMENT_ATTRIBUTES, COMMENT_STYLES))
                    self.template_value['xsrf_token'] = self.create_xsrf_token('comment')
                    self.template_value['comment_url'] = self._create_action_url(query, 'comment')

                self.template_value['endorsements'] = prefetch.prefetch_refprops(
                        Annotation.endorsements(page), Annotation.who)

                self.template_value['exemplaries'] = Annotation.exemplaries(page)

                if query['student'] == user.wiki_id:
                    self.template_value['is_author'] = True
                    self.template_value['endorsement_view'] = 'author'
                elif Annotation.endorsements(page, user).count(limit=1) > 0:
                    self.template_value['endorsement_view'] = 'has_endorsed'
                else:
                    self.template_value['endorsement_view'] = 'can_endorse'
                    self.template_value['endorse_xsrf_token'] = self.create_xsrf_token('endorse')
                    self.template_value['endorse_url'] = self._create_action_url(query, 'endorse')

            else:
                content = "The page you requested could not be found."
                self.error(404)

        self.template_value['content'] = content
        self.render("wf_page.html")

    def post_endorse(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)
        self.template_value['navbar'] = {'wiki': True}
        content = ''

        if not query:
            logging.warning("POST is not legit")
            content = "You can't do that."
            self.error(403)
            # fall through
        elif not self._can_view(query, user):
            logging.warning("Attempt to mark complete an unviewable wiki page")
            content = "You are not allowed to mark this page complete."
            self.error(403)
            # fall through
        elif user.wiki_id == query['student']:
            logging.warning("Attempt to mark own page as complete")
            content = "You are not allowed to mark this page complete."
            self.error(403)
            # fall through
        else:
            page = self._find_page(query)
            if Annotation.endorsements(page, user).count(limit=1) > 0:
                logging.warning("Attempt to mark complete multiple times.")
                content = "You've already marked this page complete."
                self.error(403)
            else:
                Annotation.endorse(page, user, 'all_done' in self.request.POST)
                self.redirect(self._create_action_url(query, 'view'))
                return
        self.template_value['content'] = content
        self.render("wf_page.html")


    def get_edit(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)
        self.template_value['navbar'] = {'wiki': True}
        self.template_value['ckeditor_allowed_content'] = (
                ckeditor.allowed_content(ALLOWED_TAGS,
                    ALLOWED_ATTRIBUTES, ALLOWED_STYLES))
        self.template_value['content'] = ''

        if not query:
            logging.info("404: query is not legit.")
            self.template_value['content'] = "The page you requested could not be found."
            self.render("wf_page.html")
            self.error(404)
            return

        editor_role = self._editor_role(query, user)
        if not editor_role:
            content = "You are not allowed to edit this student's wiki."
            self.error(403)
            # fall through
        else:
            # We call with create=True to eliminate a conditional on how
            # to set the author_name later.  But we don't .put() it.
            page = self._find_page(query, create=True)
            self.template_value['editor_role'] = editor_role
            if editor_role != 'author':
                self.template_value['navbar'] = {'participants': True}
            content = page.text or ''

            self.template_value['author_name'] = page.author.name
            self.template_value['author_link'] = student_profile_link(
                    query['student'])
            self.template_value['content'] = content
            self.template_value['xsrf_token'] = self.create_xsrf_token('save')
            self.template_value['save_url'] = self._create_action_url(query, 'save')
            self.render("wf_edit.html")
            return
        self.template_value['content'] = content
        self.render("wf_page.html")

    def get_unit(self, unit_id):
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

        if not query:
            logging.warning("POST is not legit")
            content = "You can't do that."
            self.error(403)
            # fall through
        elif not self._editor_role(query, user):
            logging.warning("Attempt to edit someone else's wiki")
            content = "You are not allowed to edit this student's wiki."
            self.error(403)
            # fall through
        elif not STUDENTS_CAN_DO_ASSIGNMENTS.value:
            logging.warning("Assignments not yet open (STUDENTS_CAN_DO_ASSIGNMENTS is false)")
            content = "Assignments are not yet available."
            self.error(403)
            # fall through
        else:
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
            return
        self.render("wf_page.html")

    def post_comment(self):
        logging.warning("In comment handler")
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)

        if not query:
            logging.warning("POST is not legit")
            content = "You can't do that."
            self.error(403)
            # fall through
        elif not self._can_comment(query, user):
            logging.warning("Attempt to comment illegally")
            content = "You are not allowed to comment on this page."
            self.error(403)
            # fall through
        else:
            page = self._find_page(query)
            comment = WikiComment(
                    author=user,
                    topic=page,
                    text=bleach_comment(self.request.get('text', '')))
            comment.put()

            if (self.request.POST.get('exemplary', False)
                    and query['student'] != user.wiki_id):
                Annotation.exemplary(page, user, comment)

            self.redirect(self._create_action_url(query, 'view'))
            return
        self.render("wf_page.html")


class WikiProfileListHandler(WikiBaseHandler):
    def get(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        self.template_value['navbar'] = {'participants': True}

        # will need to cache this somehow.
        student_list = Student.all()
        student_list.filter('is_enrolled =', True)
        student_list.order('name')

        # our course is capped at 500 students, so...
        FETCH_LIMIT=600

        self.template_value['students'] = student_list.run(
                limit=FETCH_LIMIT,
                projection=(
                    'wiki_id',
                    'name',
                    ),
                )

        self.render("wf_list.html")


class WikiProfileHandler(WikiBaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = [
            "view",
            "edit",
            ]
    post_actions = ["save"]

    class _NavForm(wtf.Form):
        student = wtf.IntegerField('Student id', [
            wtf.validators.Optional(),
            wtf.validators.NumberRange(min=1, max=100000000000),
            ])

    def _get_query(self):
        # TODO: maybe do redirects to ?student= from here?
        form = self._NavForm(self.request.params)
        if form.validate():
            return form.data
        else:
            # TODO maybe log why it's not good
            return None

    def get_view(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query()
        if not query['student']:
            self.redirect("wikiprofile?" + urllib.urlencode({
                'student': user.wiki_id}))
            return

        student_model = get_student_by_wiki_id(query['student'])

        self.template_value['navbar'] = {'wiki': True}
        self.template_value['author_name'] = student_model.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])

        profile_page = WikiPage.get_page(user=student_model, unit=None)
        if profile_page:
            self.template_value['content'] = profile_page.text
        else:
            self.template_value['content'] = "This user has not created a profile yet."

        editor_role = self._editor_role(query, user)
        self.template_value['editor_role'] = editor_role
        if editor_role != 'author':
            self.template_value['navbar'] = {'participants': True}
        self.template_value['edit_url'] = self._create_action_url(query, 'edit')

        units = self.get_units()
        pages = WikiPage.query_by_student(student_model).run(limit=100)
        units_with_pages = set([ unicode(p.unit) for p in pages ])
        for unit in units:
            if unit.unit_id in units_with_pages:
                unit._wiki_exists = True
            unit._wiki_link = "wiki?" + urllib.urlencode({
                'student': student_model.wiki_id,
                'action': 'view',
                'unit': unit.unit_id,
                })

        self.template_value['units'] = units

        self.template_value['endorsements'] = student_model.own_annotations.filter('why IN', ['endorse', 'exemplary']).run(limit=10)

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

        self.template_value['navbar'] = {'wiki': True}

        editor_role = self._editor_role(query, user)
        if not editor_role:
            self.template_value['content'] = "You are not allowed to edit this student's wiki."
            self.render("wf_page.html")
            self.error(403)
            return

        self.template_value['editor_role'] = editor_role
        self.template_value['ckeditor_allowed_content'] = (
                ckeditor.allowed_content(ALLOWED_TAGS,
                    ALLOWED_ATTRIBUTES, ALLOWED_STYLES))

        student_model = get_student_by_wiki_id(query['student'])

        self.template_value['author_name'] = student_model.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])

        self.template_value['xsrf_token'] = self.create_xsrf_token('save')
        self.template_value['save_url'] = self._create_action_url(query, 'save')

        profile_page = WikiPage.get_page(user=user, unit=None)
        if profile_page:
            self.template_value['content'] = profile_page.text

        self.render("wf_profile_edit.html")

    def post_save(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query()

        if not query:
            logging.warning("POST is not legit")
            content = "You can't do that."
            self.error(403)
            # fall through
        elif not self._editor_role(query, user):
            logging.warning("Attempt to edit someone else's wiki")
            content = "You are not allowed to edit this student's wiki."
            self.error(403)
            # fall through
        else:
            page = WikiPage.get_page(user=user, unit=None, create=True)

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
        self.render("wf_page.html")


module = None

def register_module():
    global module

    handlers = [
            ('/wiki', WikiPageHandler),
            ('/wikiprofile', WikiProfileHandler),
            ('/participants', WikiProfileListHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Wikifolios", "Wikifolio pages",
            [], handlers)

    return module

