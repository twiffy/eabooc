from models import custom_modules
from models.models import Student
from models.roles import Roles
from modules.regconf.regconf import FormSubmission
from controllers.utils import BaseHandler
from google.appengine.ext import db
import logging
import csv
import wtforms as wtf
from markupsafe import Markup

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

class CurricularAimQuery(object):
    def __init__(self, request):
        pass

    fields = ('email', 'curricular_aim')

    def run(self):
        query = FormSubmission.all().filter('form_name =', 'pre').run()
        for submission in query:
            yield {
                    'email': FormSubmission.user.get_value_for_datastore(submission).name(),
                    'curricular_aim': Markup(submission.curricular_aim),
                    }


analytics_queries = {
        'initial_curricular_aim': CurricularAimQuery,
        }


class AnalyticsHandler(BaseHandler):
    class NavForm(wtf.Form):
        query = wtf.RadioField('Analytics query',
                choices=[(k, k) for k in analytics_queries.keys()])
        view = wtf.RadioField('View',
                choices=[('csv', 'csv'), ('table', 'table')])

    def _get_nav(self):
        form = self.NavForm(self.request.GET)
        if form.validate():
            return form.data
        return None

    def get(self):
        if not Roles.is_super_admin():
            self.error(403)
            self.response.write("NO")
            return

        nav = self._get_nav()
        if not nav:
            self.render_choices_page()
            return

        query_class = analytics_queries.get(nav['query'], None)
        if not query_class:
            logging.warn("Unrecognized query")
            self.abort(404, "I couldn't find the query that you requested.")

        query = query_class(self.request)

        if nav['view'] == 'csv':
            self.render_as_csv(query.fields, query.run())
        else:
            self.render_as_table(query.fields, query.run())

    def prettify(self):
        self.personalize_page_and_get_enrolled()
        self.template_value['navbar'] = {'booctools': True}

    def render_choices_page(self):
        self.prettify()
        form_fields = Markup("<p>\n").join(
                Markup(field.label) + Markup(field) for field in self.NavForm())
        self.template_value['content'] = Markup("\n").join((
                Markup('<form action="/analytics" method="GET">'),
                form_fields,
                Markup('<input type="submit"></form>'),
                ))
        self.render('bare.html')

    def render_as_csv(self, fields, items):
        self.response.content_type = 'text/plain'

        out = csv.DictWriter(self.response, fields, extrasaction='ignore')
        out.writeheader()
        for item in items:
            for p in item.keys():
                if type(item[p]) is list:
                    item[p] = u", ".join(item[p])
                if type(item[p]) is unicode:
                    item[p] = item[p].encode('utf-8')
            out.writerow(item)

    def render_as_table(self, fields, items):
        self.prettify()
        self.template_value['fields'] = fields
        self.template_value['items'] = items
        self.render('analytics_table.html')



module = None

def register_module():
    global module

    handlers = [
            ('/student_csv', StudentCsvHandler),
            ('/analytics', AnalyticsHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Student CSV", "Student CSV",
            [], handlers)

    return module

