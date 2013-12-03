from models import custom_modules
from google.appengine.ext import deferred
from models.models import Student
from models.models import EventEntity
from models.models import StudentAnswersEntity
from models import transforms
from models.roles import Roles
from modules.regconf.regconf import FormSubmission
from modules.badges import badge_models
from controllers.utils import BaseHandler
from google.appengine.ext import db
import logging
import unicodecsv as csv
import wtforms as wtf
from markupsafe import Markup
from modules.wikifolios.wiki_models import *
import modules.wikifolios.wikifolios as wf
from modules.wikifolios.ranking import BaseRankingField
from modules.wikifolios.report import PartReport, get_part_num_by_badge_name
from modules.wikifolios.page_templates import forms, viewable_model
from collections import defaultdict, OrderedDict
from operator import itemgetter
import urllib
import re
import itertools
from common import prefetch
import plag
from common.crosstab import CrossTab
from modules.regconf import exit_survey

def find_can_use_location(student):
    conf_submission = FormSubmission.all().filter('user =', student.key()).filter('form_name =', 'conf').get()
    if conf_submission:
        return conf_submission.accept_location



class StudentCsvQuery(object):
    def __init__(self, handler):
        self.fields = sorted(Student.properties().keys() + ['email', 'can_use_location'])

    def run(self):
        for s in Student.all().run(limit=9999):
            d = db.to_dict(s)
            d['email'] = s.key().name()
            if d.get('is_participant', False):
                d['can_use_location'] = find_can_use_location(s)

            for p in d.keys():
                if type(d[p]) is list:
                    d[p] = u", ".join(d[p])
            yield d

class CurricularAimQuery(object):
    def __init__(self, handler):
        pass

    fields = ('email', 'curricular_aim')

    def run(self):
        query = FormSubmission.all().filter('form_name =', 'pre').run()
        for submission in query:
            yield {
                    'email': FormSubmission.user.get_value_for_datastore(submission).name(),
                    'curricular_aim': Markup(submission.curricular_aim),
                    }

class UnitRankingQuery(object):
    fields = ['c%d' % n for n in xrange(30)]

    def __init__(self, handler):
        unit_str = handler.request.GET['unit']
        if not unit_str:
            raise ValueError('"unit" parameter is required for this query')
        # value error may bubble up
        self.unit = int(unit_str)

    def run(self):
        pages = WikiPage.all()
        pages.filter('unit', self.unit)
        page_iter = pages.run()

        ct = CrossTab()
        vals_by_field = defaultdict(set)
        fields = [field.name for field in forms[self.unit]() if isinstance(field, BaseRankingField)]

        for page in page_iter:
            author = page.author
            ranks = {'group_id': author.group_id}
            # want to tabulate: 
            #   ranks of each item: dogs=1, cats=2, bunnies=3
            #   networking group of the student
            for field in fields:
                value = getattr(page, field)
                if not value:
                    continue
                for r in value:
                    vals_by_field[field].add(r)
                ranks.update((item, n) for n, item in enumerate(value, start=1))
            ct.add(**ranks)

        for field, values in vals_by_field.iteritems():
            yield dict(zip(self.fields, [field]))
            for v in values:
                for row in ct.table(v, 'group_id'):
                    yield dict(zip(self.fields, row))
                yield {}

class UnitRawRankingQuery(object):
    fields = ['email', 'group_id'] # extended by __init__

    def __init__(self, handler):
        unit_str = handler.request.GET['unit']
        if not unit_str:
            raise ValueError('"unit" parameter is required for this query')
        # value error may bubble up
        self.unit = int(unit_str)
        self.form_fields = [field for field in forms[self.unit]() if isinstance(field, BaseRankingField)]
        for field in self.form_fields:
            self.fields.append(field.name)
            self.fields.extend(field.choice_strings())

    def run(self):
        pages = WikiPage.all()
        pages.filter('unit', self.unit)
        page_iter = pages.run()

        for page in page_iter:
            author = page.author
            ranks = {
                    'email': author.key().name(),
                    'group_id': author.group_id,
                    }

            for f_field in self.form_fields:
                field = f_field.name
                value = getattr(page, field)
                if not value:
                    continue
                ranks.update((item, n) for n, item in enumerate(value, start=1))

            yield ranks


class UnitTextSimilarityQuery(object):
    def __init__(self, handler):
        unit_str = handler.request.GET['unit']
        if not unit_str:
            raise ValueError('"unit" parameter is required for this query')
        # value error may bubble up
        self.unit = int(unit_str)

    fields = ('10_word_phrases_in_common', 'source_1', 'source_2')

    def wikipage_to_dict(self, entity):
        info = dict()
        info['email'] = entity.author_email
        d = viewable_model(entity)
        info.update({k: re.sub(r'<[^>]*?>', '', v) for k, v in d.items()})
        return info

    def run(self):
        query = WikiPage.all().filter('unit', self.unit).run(limit=600)
        confidences = plag.find_matches(
                [self.wikipage_to_dict(p) for p in query],
                id_col='email',
                k=10)
        results = [dict(zip(self.fields, (v, k[0], k[1]))) for k,v in confidences.iteritems()]
        return sorted(results, key=itemgetter('10_word_phrases_in_common'), reverse=True)

class StudentQuizScoresQuery(object):
    def __init__(self, handler):
        pass

    fields = [
            'email',
            'assessment',
            'score',
            ] + ['q%d' % n for n in range(1, 100)]

    def run(self):
        query = StudentAnswersEntity.all().run(limit=600)
        for ans_ent in query:
            ans_dict = transforms.loads(ans_ent.data)
            for assessment, answers in ans_dict.iteritems():
                student = Student.all().filter('user_id', ans_ent.key().name()).get()
                s_scores = transforms.loads(student.scores)
                d = {
                        'email': student.key().name(),
                        'assessment': assessment,
                        'score': s_scores.get(assessment, '?????? wtf'),
                        }

                for answer in answers:
                    k = 'q%d' % (answer['index'] + 1)
                    if answer['correct']:
                        d[k] = 'correct'
                    else:
                        if isinstance(answer['value'], int):
                            d[k] = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[answer['value']]
                        else:
                            d[k] = ''

                yield d

class AllWikifolioQuery(object):
    def __init__(self, handler):
        pass

    fields = ('email', 'unit', 'endorsements')

    def run(self):
        query = WikiPage.all().run(keys_only=True)
        for page_key in query:
            if page_key.name() == 'profile':
                continue
            yield {
                    'email': page_key.parent().name(),
                    'unit': page_key.name()[5:],
                    'endorsements':  Annotation.endorsements(what=page_key).count()
                    }

class CurrentGroupIDQuery(object):
    def __init__(self, handler):
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

    def __init__(self, handler):
        request = handler.request
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
    def __init__(self, handler):
        request = handler.request
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

class StudentEditHistoryQuery(object):
    fields = [
            'recorded_on',
            'page-editor',
            'page-author',
            'unit',
            'before',
            'after',
            'is_draft',
            ]

    def __init__(self, handler):
        request = handler.request
        if 'student' not in request.GET:
            raise ValueError('Parameter required: which student? (Give their e-mail address)')
        self.student_email = request.GET['student']

    def run(self):
        # find the student's user_id..
        student = Student.get_enrolled_student_by_email(self.student_email)
        if not student:
            raise ValueError('That student was not found!')
        user_id = student.user_id
        query = EventEntity.all()
        query.filter('user_id', str(user_id))
        query.filter('source', 'edit-wiki-page')
        query.order('-recorded_on')
        edits = query.run(limit=2000)

        for edit in edits:
            fields = transforms.loads(edit.data)
            fields['recorded_on'] = edit.recorded_on
            yield fields

    def htmlize_row(self, fields):
        for field in ['before', 'after']:
            subfield_template = Markup('<h5>%s</h5>\n%s')
            new_text = Markup('\n').join(subfield_template % (k,Markup(v)) for k,v in fields[field].iteritems())
            fields[field] = new_text
        return fields


analytics_queries = OrderedDict()
analytics_queries['student_csv'] = StudentCsvQuery
analytics_queries['student_quiz_answers'] = StudentQuizScoresQuery
analytics_queries['current_group_ids'] = CurrentGroupIDQuery
analytics_queries['initial_curricular_aim'] = CurricularAimQuery
analytics_queries['unit_completion_and_full_text'] = UnitCompletionQuery
analytics_queries['unit_ranking'] = UnitRankingQuery
analytics_queries['unit_ranking_raw'] = UnitRawRankingQuery
analytics_queries['unit_all_comments'] = UnitCommentQuery
analytics_queries['unit_plagiarism_detector'] = UnitTextSimilarityQuery
analytics_queries['one_student_wiki_edit_history'] = StudentEditHistoryQuery
analytics_queries['endorsements_per_wiki_page'] = AllWikifolioQuery


class ListIncompletesQuery(object):
    fields = [
            'student',
            'unit',
            'marked_by',
            'timestamp',
            'reason',
            ]

    def __init__(self, handler):
        pass

    def run(self):
        incs = Annotation.incompletes().run()
        for inc in incs:
            d = {
                    'timestamp': inc.timestamp,
                    'reason': inc.reason,
                    }
            what_key = Annotation.what.get_value_for_datastore(inc)
            d['unit'] = what_key.name()
            d['student'] = what_key.parent().name()

            marked_by_key = Annotation.who.get_value_for_datastore(inc)
            d['marked_by'] = marked_by_key.name()
            yield d

analytics_queries['pages_marked_incomplete_by_admins'] = ListIncompletesQuery


class ExitSurveyQuery(object):
    fields = [
            'student',
            'submitted',
            ] + exit_survey.all_exit_form_db_fields

    def __init__(self, handler):
        pass

    def run(self):
        query = FormSubmission.all()
        query.filter('form_name IN', ['exit_survey_1', 'exit_survey_2', 'exit_survey_3', 'exit_survey_features'])
        query.order('user')

        for student, all_responses in itertools.groupby(query.run(),
                FormSubmission.user.get_value_for_datastore):
            # all_responses may contain more than one submission per form,
            # we need to choose the most recent one for each form.
            sorted_responses = sorted(list(all_responses),
                    key=lambda x: x.submitted, reverse=True)

            row = {'student': student.name()}
            seen = set()

            for response in sorted_responses:
                if response.form_name not in seen:
                    row.update(db.to_dict(response))
                    seen.add(response.form_name)

            yield row

analytics_queries['exit_survey'] = ExitSurveyQuery


class BadgeAssertionQuery(object):
    fields = [
            'badge_name',
            'recipient',
            'email',
            'group_id',
            'issuedOn',
            'endorsements',
            'promotions',
            'comments',
            'expires',
            'revoked',
            'evidence',
            'id',
            ]
    exclude_revoked = True

    def __init__(self, handler):
        self.handler = handler

    def run(self):
        asserts = badge_models.BadgeAssertion.all()
        if self.exclude_revoked:
            asserts.filter('revoked', False)
        for ass in asserts.run():
            d = {}
            for f in ['issuedOn', 'expires', 'revoked', 'evidence']:
                d[f] = getattr(ass, f)

            d['badge_name'] = ass.badge_name
            student = ass.recipient
            d['recipient'] = student.badge_name
            d['email'] = student.key().name()
            d['group_id'] = student.group_id
            d['id'] = ass.key().id()

            part_num = get_part_num_by_badge_name(ass.badge_name)
            report = PartReport.on(student, self.handler.get_course(), part_num)
            unit_reps = report.unit_reports
            for attr in ['endorsements', 'promotions', 'comments']:
                d[attr] = sum(getattr(u, attr) for u in unit_reps)

            yield d

class BadgeAssertionQueryWithRevoked(BadgeAssertionQuery):
    def __init__(self, handler):
        super(BadgeAssertionQueryWithRevoked, self).__init__(handler)
        self.exclude_revoked = False

analytics_queries['badge_assertions'] = BadgeAssertionQuery
analytics_queries['badge_assertions_with_revoked'] = BadgeAssertionQueryWithRevoked


class UnenrollSurveyQuery(object):
    fields = [
            # from us
            'email',
            'wikis_posted',

            # from the form
            'how_found_out',
            'how_found_out_other',
            'difficulty',
            'communication',
            'better_communication',
            'other_comments',
            ]

    def __init__(self, handler):
        pass

    def run(self):
        query = EventEntity.all()
        query.filter('source', 'unenrolled')
        query.order('-recorded_on')

        for survey in query.run():
            yield transforms.loads(survey.data)

analytics_queries['unenroll_survey'] = UnenrollSurveyQuery


class AnalyticsHandler(BaseHandler):
    class NavForm(wtf.Form):
        query = wtf.RadioField('Analytics query',
                choices=[(k, k) for k in analytics_queries.keys()])
        view = wtf.RadioField('View',
                choices=[('csv', 'csv'), ('table', 'table'), ('debug', 'debug')],
                default='table')
        unit = wtf.IntegerField('Unit Number (for unit queries)',
                [wtf.validators.Optional()])
        student = wtf.StringField('Student email (for edit history query)',
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
            query = query_class(self)
        except ValueError as e:
            self.render_choices_page(error=e.message)
            return

        if nav['view'] == 'csv':
            self.render_as_csv(query.fields, query.run())
        elif nav['view'] == 'debug':
            i = query.run()
            for x in i:
                pass
        else:
            iterator = query.run()
            if hasattr(query_class, 'htmlize_row'):
                iterator = [query.htmlize_row(r) for r in iterator]
            self.render_as_table(query.fields, iterator)

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
            ('/analytics', AnalyticsHandler),
            ('/adminjob', JobsHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Student CSV", "Student CSV",
            [], handlers)

    return module

