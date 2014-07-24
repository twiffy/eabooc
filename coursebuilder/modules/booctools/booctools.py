"""
Just render the "booc tools!" page!
"""
from modules.regconf.regconf import get_student_count
from models import custom_modules
from controllers.utils import BaseHandler
from models.roles import Roles
import logging
import os.path

class BoocToolsHandler(BaseHandler):
    def get(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return
        if not Roles.is_course_admin(self.app_context):
            self.abort(403)
        self.template_value['student_count'] = get_student_count()
        self.template_value['navbar'] = {'booctools': True}
        self.render('booctools.html')




module = None

def register_module():
    global module

    handlers = [
            ('/booctools', BoocToolsHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("BoocTools", "BOOC Tools Page",
            [], handlers)

    return module

