"""
Wikifolios module for Google Course Builder
"""

from models import custom_modules
import bleach
import webapp2
from controllers.utils import BaseHandler, ReflectiveRequestHandler

class TestHandler(BaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = "view"

    def get_view(self):
        user = self.personalize_page_and_get_enrolled()
        self.template_value['content'] = bleach.clean('an <script>evil()</script> example')
        self.template_value['navbar'] = {'wiki': True}

        self.render("wf_page.html")

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

