from models import custom_modules
from models.models import Student
from models.roles import Roles
from controllers.utils import BaseHandler
from google.appengine.ext import db
import logging
import csv


class StudentCsvHandler(BaseHandler):
    def get(self):
        self.response.content_type = 'text/plain'

        if not Roles.is_super_admin():
            self.error(403)
            self.response.write("NO")
            return

        props = sorted(Student.properties().keys() + ['email',])
        out = csv.DictWriter(self.response, props, extrasaction='ignore')
        out.writeheader()
        for s in Student.all().run(limit=9999):
            d = db.to_dict(s)
            d['email'] = s.key().name()
            for p in d.keys():
                if type(d[p]) is list:
                    d[p] = ", ".join(d[p])
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

