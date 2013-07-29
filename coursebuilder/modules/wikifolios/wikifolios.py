"""
Wikifolios module for Google Course Builder
"""

from models import custom_modules
import bleach
import webapp2
from controllers.utils import BaseHandler, ReflectiveRequestHandler
from modules.wikifolios.wiki_models import WikiPage

class TestHandler(BaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = ["view", "edit"]
    post_actions = ["save"]

    def get_view(self):
        user = self.personalize_page_and_get_enrolled()
        content = None

        page = WikiPage.get_by_key_name("test")
        if page:
            content = page.text
        if not content:
            content = bleach.clean('an <script>evil()</script> example')
        self.template_value['content'] = content
        self.template_value['can_edit'] = True
        self.template_value['navbar'] = {'wiki': True}
        self.render("wf_page.html")

    def get_edit(self):
        user = self.personalize_page_and_get_enrolled()
        page = WikiPage.get_by_key_name("test")
        if page:
            content = page.text
        else:
            content = ''
        self.template_value['content'] = content
        self.template_value['navbar'] = {'wiki': True}
        self.template_value['xsrf_token'] = self.create_xsrf_token('save')
        self.render("wf_edit.html")

    def post_save(self):
        user = self.personalize_page_and_get_enrolled()
        page = WikiPage.get_by_key_name("test")
        if not page:
            page = WikiPage(key_name="test")
        page.text = bleach.clean(self.request.get('text', ''))
        page.put()
        self.redirect("wiki")



module = None

def register_module():
    global module

    handlers = [
            ('/wiki', TestHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Wikifolios", "Wikifolio pages",
            [], handlers)

    return module

