from models import custom_modules
from models.models import Student
from models.roles import Roles
from modules.regconf.regconf import FormSubmission
from controllers.utils import BaseHandler
from google.appengine.ext import db
import logging
import csv

def find_can_use_location(student):
    conf_submission = FormSubmission.all().filter('user =', student.key()).filter('form_name =', 'conf').get()
    if conf_submission:
        return conf_submission.accept_location



class StudentCsvHandler(BaseHandler):
    def get(self):
        self.response.content_type = 'text/plain'

        if not Roles.is_super_admin():
            self.error(403)
            self.response.write("NO")
            return

        props = sorted(Student.properties().keys() + ['email', 'can_use_location'])
        out = csv.DictWriter(self.response, props, extrasaction='ignore')
        out.writeheader()
        for s in Student.all().run(limit=9999):
            d = db.to_dict(s)
            d['email'] = s.key().name()
            if d.get('is_participant', False):
                d['can_use_location'] = find_can_use_location(s)

            for p in d.keys():
                if type(d[p]) is list:
                    d[p] = u", ".join(d[p])
                # note that I just changed the type from list to unicode...
                if type(d[p]) is unicode:
                    d[p] = d[p].encode('utf-8')
            out.writerow(d)


module = None

def register_module():
    global module

    handlers = [
            ('/student_csv', StudentCsvHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Student CSV", "Student CSV",
            [], handlers)

    return module

