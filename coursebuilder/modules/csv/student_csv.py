from models import custom_modules
from google.appengine.ext import deferred
from models.models import Student
from models.roles import Roles
from modules.regconf.regconf import FormSubmission
from controllers.utils import BaseHandler
from google.appengine.ext import db
import logging
import unicodecsv as csv
import wtforms as wtf
from markupsafe import Markup
from modules.wikifolios.wiki_models import *
from modules.wikifolios.page_templates import forms, viewable_model
import urllib
import re

def find_can_use_location(student):
    conf_submission = FormSubmission.all().filter('user =', student.key()).filter('form_name =', 'conf').get()
    if conf_submission:
        return conf_submission.accept_location



class StudentCsvHandler(BaseHandler):
    def get(self):
        self.response.content_type = 'text/plain'

        if not Roles.is_course_admin(self.app_context):
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
                #if type(d[p]) is unicode:
                    #d[p] = d[p].encode('utf-8')
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



class UnitCompletionQuery(object):
    def __init__(self, request):
        self.request = request
        unit_str = request.GET['unit']
        if not unit_str:
            raise ValueError('"unit" parameter is required for this query')
        # value error may bubble up
        self.unit = int(unit_str)
        self.fields = [
                'email',
                'name',
                'unit',
                'group_id',
                'posted_unit',
                'exemplaries_received',
                'exemplaries_given',
                'endorsements_received',
                'endorsements_given',
                'num_comments',
                'link',
                ]
        self.fields.extend(field.name for field in forms[self.unit]())

    def run(self):
        query = Student.all().filter('is_participant =', True).run(limit=600)
        unit = self.unit
        for student in query:
            # TODO use defaultdict('') instead of local vars?
            unit_page = WikiPage.get_page(student, unit=unit)
            posted_unit = bool(unit_page)
            num_endorsements = num_exemplaries = num_comments = ''
            if unit_page:
                num_endorsements = Annotation.endorsements(what=unit_page).count()
                num_exemplaries = Annotation.exemplaries(what=unit_page).count()
                num_comments = WikiComment.all().filter('topic', unit_page).count()
                fields = viewable_model(unit_page)
            else:
                fields = {}

            num_given = Annotation.endorsements(who=student, unit=unit).count()
            exemps_given = Annotation.exemplaries(who=student, unit=unit).count()

            info = {
                    'email': student.key().name(),
                    'name': student.name,
                    'unit': unit,
                    'group_id': student.group_id,
                    'posted_unit': posted_unit,
                    'endorsements_received': num_endorsements,
                    'endorsements_given': num_given,
                    'exemplaries_received': num_exemplaries,
                    'exemplaries_given': exemps_given,
                    'num_comments': num_comments,
                    'link': Markup('<a href="%s%s?%s">link</a>') % (
                        self.request.host_url,
                        '/wiki',
                        urllib.urlencode({
                            'unit': unit,
                            'student': student.wiki_id,
                            'action': 'view'
                            })),
                    }
            info.update({k: re.sub(r'<[^>]*?>', '', v) for k, v in fields.items()})
            #info.update(fields)
            yield info

analytics_queries = {
        'initial_curricular_aim': CurricularAimQuery,
        'unit_completion': UnitCompletionQuery,
        }


class AnalyticsHandler(BaseHandler):
    class NavForm(wtf.Form):
        query = wtf.RadioField('Analytics query',
                choices=[(k, k) for k in analytics_queries.keys()])
        view = wtf.RadioField('View',
                choices=[('csv', 'csv'), ('table', 'table')],
                default='table')
        unit = wtf.IntegerField('Unit Number (for unit completion query)',
                [wtf.validators.Optional()])

    def _get_nav(self):
        form = self.NavForm(self.request.GET)
        if form.validate():
            return form.data
        return None

    def get(self):
        if not Roles.is_course_admin(self.app_context):
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

        try:
            query = query_class(self.request)
        except ValueError as e:
            self.render_choices_page(error=e.message)
            return

        if nav['view'] == 'csv':
            self.render_as_csv(query.fields, query.run())
        else:
            self.render_as_table(query.fields, query.run())

    def prettify(self):
        self.personalize_page_and_get_enrolled()
        self.template_value['navbar'] = {'booctools': True}

    def render_choices_page(self, error=''):
        self.prettify()
        form_fields = Markup("<p>\n").join(
                Markup(field.label) + Markup(field) for field in self.NavForm())
        self.template_value['content'] = Markup('''
                <div class="gcb-aside">
                <div style="background-color: #fcc;">%s</div>
                <form action="/analytics" method="GET">
                %s
                <br><input type="submit" value="Run">
                </form>
                </div>
                ''') % (error, form_fields)
        self.render('bare.html')

    def render_as_csv(self, fields, items):
        self.response.content_type = 'text/plain'

        out = csv.DictWriter(self.response, fields, extrasaction='ignore')
        out.writeheader()
        for item in items:
            for p in item.keys():
                if type(item[p]) is list:
                    item[p] = u", ".join(item[p])
                #if type(item[p]) is unicode:
                    #item[p] = item[p].encode('utf-8')
            out.writerow(item)

    def render_as_table(self, fields, items):
        self.prettify()
        self.template_value['fields'] = fields
        self.template_value['items'] = items
        self.render('analytics_table.html')

class JobsHandler(BaseHandler):
    def get(self):
        if not Roles.is_course_admin(self.app_context):
            self.abort(403)
        from modules.csv import jobs
        job = jobs.the_job()
        deferred.defer(job.run)



module = None

def register_module():
    global module

    handlers = [
            ('/student_csv', StudentCsvHandler),
            ('/analytics', AnalyticsHandler),
            ('/adminjob', JobsHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Student CSV", "Student CSV",
            [], handlers)

    return module

