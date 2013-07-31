"""
Wikifolios module for Google Course Builder
"""

from models import custom_modules
from models.models import Student
from common import ckeditor
import bleach
import webapp2
from controllers.utils import BaseHandler, ReflectiveRequestHandler
from modules.wikifolios.wiki_models import WikiPage
import logging
import urllib
import wtforms as wtf

class WikiNavForm(wtf.Form):
    unit = wtf.IntegerField('Unit number', [
        wtf.validators.NumberRange(min=1, max=100),
        ])
    student = wtf.IntegerField('Student id', [
        wtf.validators.Optional(),
        wtf.validators.NumberRange(min=1, max=100000000000),
        ])

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
            attributes=ALLOWED_ATTRIBUTES ,
            styles=ALLOWED_STYLES,
            )

class WikiPageHandler(BaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = ["view", "edit"]
    post_actions = ["save"]

    def _get_query(self):
        form = WikiNavForm(self.request.params)
        if form.validate():
            return form.data
        else:
            # TODO maybe log why it's not good
            return None

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

    def get_view(self):
        student = self.personalize_page_and_get_enrolled()
        if not student:
            return
        query = self._get_query()
        self.template_value['navbar'] = {'wiki': True}
        self.template_value['content'] = ''

        if not query:
            logging.info("404: query is not legit.")
            content = "The page you requested could not be found."
            self.error(404)
            # fall through
        elif not query['student']:
            query['student'] = student.wiki_id
            self.redirect(self._create_action_url(query, 'view'))
            return
        else:
            # Want the edit link even if the page doesn't exist, so they
            # can create it.
            # TODO if user is admin, it's ok after all
            page_author_is_viewer = query['student'] == student.wiki_id
            self.template_value['can_edit'] = page_author_is_viewer
            self.template_value['edit_url'] = self._create_action_url(query, 'edit')

            page = self._find_page(query)
            if page:
                content = page.text
                author_name = page.author.name + (
                        " (you)" if page_author_is_viewer else "")
                self.template_value['author_name'] = author_name
                self.template_value['author_link'] = student_profile_link(
                        query['student'])
            else:
                content = "The page you requested could not be found."
                self.error(404)

        self.template_value['content'] = content
        # TODO put access check into model? or at least own function.
        self.render("wf_page.html")

    def get_edit(self):
        student = self.personalize_page_and_get_enrolled()
        if not student:
            return
        query = self._get_query()
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
        elif not query['student']:
            query['student'] = student.wiki_id
            self.redirect(self._create_action_url(query, 'edit'))
            return
        elif query['student'] != student.wiki_id:
            # TODO if user is admin, it's ok after all
            content = "You are not allowed to edit this student's wiki."
            self.error(403)
        else:
            page = self._find_page(query)
            if page:
                content = page.text
            else:
                content = ''
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

    def post_save(self):
        student = self.personalize_page_and_get_enrolled()
        if not student:
            return
        query = self._get_query()

        if not query:
            logging.warning("POST is not legit")
            content = "You can't do that."
            self.error(403)
        elif query['student'] != student.wiki_id:
            # TODO if user is admin, it's ok
            # (make sure to handle empty query['student'])
            logging.warning("Attempt to edit someone else's wiki")
            content = "You are not allowed to edit this student's wiki."
            self.error(403)
        else:
            page = self._find_page(query, create=True)

            page.text = bleach_entry(self.request.get('text', ''))
            page.unit = query['unit']

            page.put()
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
        form = self._NavForm(self.request.params)
        if form.validate():
            return form.data
        else:
            # TODO maybe log why it's not good
            return None

    def get_view(self):
        student = self.personalize_page_and_get_enrolled()
        if not student:
            return
        query = self._get_query()
        if not query['student']:
            query['student'] = student.wiki_id

        student_model = get_student_by_wiki_id(query['student'])

        self.template_value['navbar'] = {'wiki': True}
        self.template_value['author_name'] = student_model.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])

        self.template_value['content'] = "(here is some <i>html</i>)"

        pages = WikiPage.query_by_student(student_model).run(limit=100)
        def linkified(page):
            page._link = "wiki?" + urllib.urlencode({
                'student': student_model.wiki_id,
                'action': 'view',
                'unit': page.unit,
                })
            return page
        self.template_value['wiki_pages'] = [linkified(p) for p in pages]
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

