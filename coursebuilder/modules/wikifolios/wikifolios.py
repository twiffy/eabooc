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
        wtf.validators.Optional(),
        wtf.validators.NumberRange(min=1, max=100),
        ])
    student = wtf.IntegerField('Student id', [
        wtf.validators.Optional(),
        wtf.validators.NumberRange(min=1, max=100000000000),
        ])

class WikiHandler(BaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = ["view", "edit"]
    post_actions = ["save"]

    def _set_nav(self):
        form = WikiNavForm(self.request.params)
        if form.validate():
            self.query = form.data
        else:
            self.query = {}

    def _find_page(self, student, create=False):
        logging.info(self.query)
        if 'student' in self.query:
            page_student = (Student.all()
                    .filter("wiki_id =", self.query['student'])
                    .get())
            # OK if that returns None, we want to 404.
        else:
            page_student = student

        logging.info('page student %s', page_student)

        key = WikiPage.get_key(page_student, self.query.get('unit', None))
        if not key:
            # Not only is there no page,
            # but the request is invalid too.
            return None

        page = WikiPage.get(key)
        if (not page) and create:
            page = WikiPage(key=key)

        return page

    def _create_action_url(self, action="view"):
        unit = self.query.get('unit', '')
        params = {
                'action': action,
                'unit': unit,
                }
        return '?'.join((
                self.request.path,
                urllib.urlencode(params)))

    def get_view(self):
        student = self.personalize_page_and_get_enrolled()
        student.ensure_wiki_id()
        self._set_nav()
        content = None

        page = self._find_page(student)
        if page:
            content = page.text
        if not content:
            content = "The page you requested could not be found."
            self.error(404)
        self.template_value['content'] = content
        self.template_value['can_edit'] = True
        self.template_value['edit_url'] = self._create_action_url('edit')
        self.template_value['navbar'] = {'wiki': True}
        self.render("wf_page.html")

    def get_edit(self):
        student = self.personalize_page_and_get_enrolled()
        student.ensure_wiki_id()
        self._set_nav()

        # shit, don't want to consider the requested student here.
        # have to think this through harder :(
        page = self._find_page(student)
        if page:
            content = page.text
        else:
            content = ''
        self.template_value['content'] = content
        self.template_value['unit'] = self.query.get('unit', '')
        self.template_value['navbar'] = {'wiki': True}
        self.template_value['xsrf_token'] = self.create_xsrf_token('save')
        self.render("wf_edit.html")

    def post_save(self):
        student = self.personalize_page_and_get_enrolled()
        student.ensure_wiki_id()
        self._set_nav()

        page = self._find_page(student, create=True)

        page.text = bleach.clean(self.request.get('text', ''))
        page.unit = self.query.get('unit', None)

        page.put()
        self.redirect(self._create_action_url('view'))



module = None

def register_module():
    global module

    handlers = [
            ('/wiki', WikiHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Wikifolios", "Wikifolio pages",
            [], handlers)

    return module

