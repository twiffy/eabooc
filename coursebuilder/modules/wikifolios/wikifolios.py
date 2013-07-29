"""
Wikifolios module for Google Course Builder
"""

from models import custom_modules
from models.models import Student
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
        # optimize this.
        student_model = (Student.all()
                .filter("wiki_id =", query['student'])
                .get())
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
            self.template_value['can_edit'] = query['student'] == student.wiki_id
            self.template_value['edit_url'] = self._create_action_url(query, 'edit')

            page = self._find_page(query)
            if page:
                content = page.text
            else:
                content = "The page you requested could not be found."
                self.error(404)

        self.template_value['content'] = content
        # TODO put access check into model? or at least own function.
        self.render("wf_page.html")

    def get_edit(self):
        student = self.personalize_page_and_get_enrolled()
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
            self.template_value['content'] = content
            self.template_value['xsrf_token'] = self.create_xsrf_token('save')
            self.template_value['save_url'] = self._create_action_url(query, 'save')
            self.render("wf_edit.html")
            return
        self.template_value['content'] = content
        self.render("wf_page.html")

    def post_save(self):
        student = self.personalize_page_and_get_enrolled()
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

            page.text = bleach.clean(self.request.get('text', ''))
            page.unit = query['unit']

            page.put()
            self.redirect(self._create_action_url(query, 'view'))
            return
        self.render("wf_page.html")


class WikiProfileHandler(BaseHandler, ReflectiveRequestHandler):
    pass

module = None

def register_module():
    global module

    handlers = [
            ('/wiki', WikiPageHandler),
            ('/wiki/profile', WikiProfileHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Wikifolios", "Wikifolio pages",
            [], handlers)

    return module

