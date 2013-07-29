"""
Wikifolios module for Google Course Builder
"""

from models import custom_modules
import bleach
import webapp2
from controllers.utils import BaseHandler, ReflectiveRequestHandler
from modules.wikifolios.wiki_models import WikiPage
import logging
import urllib
import wtforms as wtf

class WikiNavForm(wtf.Form):
    unit = wtf.IntegerField()

def try_parse_int(s, default=None, base=10):
    try:
        return int(s, base)
    except ValueError:
        return default

class WikiHandler(BaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = ["view", "edit"]
    post_actions = ["save"]

    def _set_unit(self):
        form = WikiNavForm(self.request.params)
        if form.validate():
            self.unit = form.unit.data
        else:
            self.unit = None

    def _find_page(self, student, create=False):
        key = WikiPage.get_key(student, self.unit)

        page = WikiPage.get(key)
        if (not page) and create:
            page = WikiPage(key=key)

        return page

    def _create_action_url(self, action="view"):
        unit = ''
        if self.unit:
            unit = self.unit
        params = {
                'action': action,
                'unit': unit,
                }
        return '?'.join((
                self.request.path,
                urllib.urlencode(params)))

    def get_view(self):
        student = self.personalize_page_and_get_enrolled()
        self._set_unit()
        content = None

        page = self._find_page(student)
        if page:
            content = page.text
        if not content:
            content = bleach.clean('(no page here yet)')
        self.template_value['content'] = content
        self.template_value['can_edit'] = True
        self.template_value['edit_url'] = self._create_action_url('edit')
        self.template_value['navbar'] = {'wiki': True}
        self.render("wf_page.html")

    def get_edit(self):
        student = self.personalize_page_and_get_enrolled()
        self._set_unit()

        page = self._find_page(student)
        if page:
            content = page.text
        else:
            content = ''
        self.template_value['content'] = content
        self.template_value['unit'] = self.unit
        self.template_value['navbar'] = {'wiki': True}
        self.template_value['xsrf_token'] = self.create_xsrf_token('save')
        self.render("wf_edit.html")

    def post_save(self):
        student = self.personalize_page_and_get_enrolled()
        self._set_unit()
        page = self._find_page(student, create=True)

        page.text = bleach.clean(self.request.get('text', ''))
        page.unit = self.unit

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

