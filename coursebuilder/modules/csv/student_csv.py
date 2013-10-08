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
import modules.wikifolios.wikifolios as wf
from modules.wikifolios.page_templates import forms, viewable_model
from collections import defaultdict
import urllib
import re
import itertools
from common import prefetch
import plag

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

class UnitTextSimilarityQuery(object):
    def __init__(self, request):
        unit_str = request.GET['unit']
        if not unit_str:
            raise ValueError('"unit" parameter is required for this query')
        # value error may bubble up
        self.unit = int(unit_str)

    fields = ('10_word_phrases_in_common', 'source_1', 'source_2')

    def wikipage_to_dict(self, entity):
        info = dict()
        info['email'] = entity.author_email
        d = db.to_dict(entity)
        info.update({k: re.sub(r'<[^>]*?>', '', v) for k, v in d.items()})
        return info

    def run(self):
        query = WikiPage.all().filter('unit', self.unit).run(limit=600)
        confidences = plag.find_matches(
                [self.wikipage_to_dict(p) for p in query],
                id_col='email',
                k=10)
        return [(v, k[0], k[1]) for k,v in confidences.iteritems()]


class CurrentGroupIDQuery(object):
    def __init__(self, request):
        pass

    fields = ('email', 'group_id')

    def run(self):
        query = Student.all().filter('is_participant', True).run(limit=600)
        for student in query:
            yield {
                    'email': student.key().name(),
                    'group_id': student.group_id,
                    }

class UnitCommentQuery(object):
    fields = [
            'orig_row_number',
            'link',
            'unit',
            'page_author',
            'comment_author',
            'is_reply',
            'added_time',
            'is_edited',
            'is_deleted',
            'text',
            ]

    def __init__(self, request):
        self.request = request
        unit_str = request.GET['unit']
        if not unit_str:
            raise ValueError('"unit" parameter is required for this query')
        # value error may bubble up
        self.unit = int(unit_str)

    def run(self):
        counter = itertools.count(1)
        pages = WikiPage.all().filter('unit', self.unit).run(limit=600)
        prefetcher = prefetch.CachingPrefetcher()
        for page in pages:
            comments = page.comments.run(limit=100)
            page_author = "%s (%s)" % (page.author.name, page.author_email)
            prefetcher.add(page.author)

            for comment in wf.sort_comments(
                    prefetcher.prefetch(comments, WikiComment.author)):
                row = defaultdict(str)
                row['orig_row_number'] = next(counter)
                row['page_author'] = page_author
                row['link'] = self.request.host_url + '/' + wf.comment_permalink(comment)
                row['comment_author'] = "%s (%s)" % (comment.author.name, comment.author_email)
                row['unit'] = page.unit
                row['is_reply'] = comment.is_reply()
                for attr in ['added_time', 'text']:
                    row[attr] = getattr(comment, attr)
                for attr in ['is_edited', 'is_deleted']:
                    row[attr] = bool(getattr(comment, attr))
                row['text'] = re.sub(r'<[^>]*?>', '', row['text'])
                yield row


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
        'unit_comments': UnitCommentQuery,
        'current_group_ids': CurrentGroupIDQuery,
        'unit_text_similarity': UnitTextSimilarityQuery
        }


class AnalyticsHandler(BaseHandler):
    class NavForm(wtf.Form):
        query = wtf.RadioField('Analytics query',
                choices=[(k, k) for k in sorted(analytics_queries.keys())])
        view = wtf.RadioField('View',
                choices=[('csv', 'csv'), ('table', 'table')],
                default='table')
        unit = wtf.IntegerField('Unit Number (for unit queries)',
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
        self.response.content_type = 'text/csv; charset=UTF-8'
        self.response.headers['Content-Disposition'] = 'attachment;filename=analytics.csv'

        self.response.write(u'\ufeff')
        out = csv.DictWriter(self.response, fields, extrasaction='ignore')
        out.writeheader()
        for item in items:
            for p in item.keys():
                if type(item[p]) is list:
                    item[p] = u", ".join(item[p])
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

