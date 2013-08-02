"""
Wikifolios module for Google Course Builder
"""

from models import custom_modules
from models.models import Student
from models.roles import Roles
from common import ckeditor
import bleach
import webapp2
from controllers.utils import BaseHandler, ReflectiveRequestHandler
from modules.wikifolios.wiki_models import WikiPage, WikiComment
from google.appengine.api import users
import logging
import urllib
import wtforms as wtf

def get_student_by_wiki_id(wiki_id):
    return (Student.all()
            .filter("wiki_id =", wiki_id)
            .get())

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
    return bleach.clean(html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            styles=ALLOWED_STYLES,
            )

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


class WikiPageHandler(BaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = ["view", "edit"]
    post_actions = ["save", "comment"]

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

    def _create_action_url(self, query, action="view"):
        params = {
                'action': action,
                'unit': query['unit'],
                'student': query['student'],
                }
        return '?'.join((
                self.request.path,
                urllib.urlencode(params)))

    def _can_view(self, query, current_student):
        if current_student:
            assert current_student.key().name() == users.get_current_user().email()
        is_enrolled = (current_student and current_student.is_enrolled)
        return is_enrolled or Roles.is_course_admin()

    def _can_edit(self, query, current_student):
        if current_student:
            assert current_student.key().name() == users.get_current_user().email()
        is_author = (current_student
                and current_student.wiki_id == query['student']
                and current_student.is_enrolled)
        return is_author or Roles.is_course_admin()

    def _can_comment(self, query, current_student):
        return self._can_view(query, current_student)

    def get_view(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return
        query = self._get_query(user)
        self.template_value['navbar'] = {'wiki': True}
        self.template_value['content'] = ''

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
            self.template_value['can_edit'] = self._can_edit(query, user)
            self.template_value['edit_url'] = self._create_action_url(query, 'edit')
            self.template_value['unit'] = list([u for u in self.get_units() if u.unit_id == unicode(query['unit'])])[0]

            page = self._find_page(query)
            if page:
                content = page.text
                author_name = page.author.name
                self.template_value['author_name'] = author_name
                self.template_value['author_link'] = student_profile_link(
                        query['student'])
                self.template_value['comments'] = page.comments.order("added_time")
                if self._can_comment(query, user):
                    self.template_value['can_comment'] = True
                    self.template_value['ckeditor_comment_content'] = (
                            ckeditor.allowed_content(COMMENT_TAGS,
                                COMMENT_ATTRIBUTES, COMMENT_STYLES))
                    self.template_value['xsrf_token'] = self.create_xsrf_token('comment')
                    self.template_value['comment_url'] = self._create_action_url(query, 'comment')
            else:
                content = "The page you requested could not be found."
                self.error(404)

        self.template_value['content'] = content
        self.render("wf_page.html")

    def get_edit(self):
        user = self.personalize_page_and_get_enrolled()
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
            content = "The page you requested could not be found."
            self.error(404)
            # fall through
        elif not self._can_edit(query, user):
            content = "You are not allowed to edit this student's wiki."
            self.error(403)
            # fall through
        else:
            page = self._find_page(query)
            if page:
                content = page.text
                self.template_value['author_name'] = page.author.name
            else:
                content = ''
                self.template_value['author_name'] = user.name
            self.template_value['author_link'] = student_profile_link(
                    query['student'])
            self.template_value['content'] = content
            self.template_value['xsrf_token'] = self.create_xsrf_token('save')
            self.template_value['save_url'] = self._create_action_url(query, 'save')
            self.render("wf_edit.html")
            return
        self.template_value['content'] = content
        self.render("wf_page.html")

    def post_save(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return
        query = self._get_query(user)

        if not query:
            logging.warning("POST is not legit")
            content = "You can't do that."
            self.error(403)
            # fall through
        elif not self._can_edit(query, user):
            logging.warning("Attempt to edit someone else's wiki")
            content = "You are not allowed to edit this student's wiki."
            self.error(403)
            # fall through
        else:
            page = self._find_page(query, create=True)

            page.text = bleach_entry(self.request.get('text', ''))
            page.unit = query['unit']

            page.put()
            self.redirect(self._create_action_url(query, 'view'))
            return
        self.render("wf_page.html")

    def post_comment(self):
        logging.warning("In comment handler")
        user = self.personalize_page_and_get_enrolled()
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

            self.redirect(self._create_action_url(query, 'view'))
            return
        self.render("wf_page.html")



class WikiProfileHandler(BaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = [
            "view",
            #"edit",
            ]
    #post_actions = ["save"]

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
        user = self.personalize_page_and_get_enrolled()
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

        self.template_value['content'] = "(here is some <i>html</i>)"

        self.render("wf_profile.html")

module = None

def register_module():
    global module

    handlers = [
            ('/wiki', WikiPageHandler),
            ('/wikiprofile', WikiProfileHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Wikifolios", "Wikifolio pages",
            [], handlers)

    return module

