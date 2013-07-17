"""
Wikifolios module for Google Course Builder
"""

from models import custom_modules
import bleach
import webapp2

class TestHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("Hey, maybe it works!")
        self.response.write(
                bleach.clean('an <script>evil()</script> example')
                )

module = None

def register_module():
    global module

    handlers = [
            ('/test', TestHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Wikifolios", "Wikifolio pages",
            [], handlers)

    return module

