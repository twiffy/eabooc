"""
An enormous collection of queries into the state of the course, and students'
activities.  Also, the request handlers that run the queries when the course
admins request them.

There are two kinds of query - "classic queries" that inherit from `object`,
and run by calling .run(), and "fancy queries" that inherit from
common.TableMakerMapper.  The "classic" ones are limited by the time they
can take - 60 seconds.  You also have to decide whether you want an html table
or a CSV file at the time you start the query.  Fancy ones, on the other hand,
don't have these restrictions, but are slightly more limited in the kind of
queries they can run - they have to iterate over some kind of model object.

To make it onto the menu for a user to run it, an entry needs to be defined in
either the 'mapper_queries' or 'analytics_queries' dicts.
"""
from models import custom_modules
from common.querymapper import TableMakerMapper, TableMakerResult
from controllers.utils import ReflectiveRequestHandler
from google.appengine.api import users
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
from common import edit_distance

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

class FixedUnitRankingQuery(TableMakerMapper):
    FIELDS = ['c%d' % n for n in xrange(30)]

    KIND = WikiPage
    FILTERS = []

    def __init__(self, **kwargs):
        self.unit = kwargs['unit']
        if not self.unit:
            raise ValueError('"unit" parameter is required for this query')
        self.FILTERS = [('unit', self.unit)]
        self.ct = CrossTab()
        self.vals_by_field = defaultdict(set)
        self.ranking_fields = [field.name for field in forms[self.unit]() if isinstance(field, BaseRankingField)]
        super(FixedUnitRankingQuery, self).__init__()

    def map(self, page):
        author = page.author
        # want to tabulate:
        #   ranks of each item: dogs=1, cats=2, bunnies=3
        #   networking group of the student
        for field in self.ranking_fields:
            ranks = {'group_id': author.group_id}
            value = getattr(page, field)
            if not value:
                continue
            for r in value:
                self.vals_by_field[field].add(r)
            ranks.update((item, n) for n, item in enumerate(value, start=1))
            self.ct.add(**ranks)

    def finish(self):
        # go over each field of the page
        for field, values in self.vals_by_field.iteritems():
            self.add_row(dict(zip(self.FIELDS, [field])))
            # Go over each value, giving its rankings
            for v in values:
                for row in self.ct.table(v, 'group_id'):
                    self.add_row(dict(zip(self.FIELDS, row)))
                self.add_row({})


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
#analytics_queries['unit_ranking'] = UnitRankingQuery # use FixedUnitRanking now.
analytics_queries['unit_ranking_raw'] = UnitRawRankingQuery
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

class TableRenderingHandler(BaseHandler):
    def render_as_csv(self, fields, items):
        self.response.content_type = 'text/csv; charset=UTF-8'
        self.response.headers['Content-Disposition'] = 'attachment;filename=analytics.csv'

        self.response.write(u'\ufeff')
        out = csv.DictWriter(self.response, fields, extrasaction='ignore')
        out.writeheader()
        for item in items:
            for p in item.keys():
                if type(item[p]) is list:
                    item[p] = u", ".join([unicode(i) for i in item[p]])
            out.writerow(item)

    def render_as_table(self, fields, items):
        self.prettify()
        self.template_value['fields'] = fields
        self.template_value['items'] = items
        self.render('analytics_table.html')

    def prettify(self):
        self.personalize_page_and_get_enrolled()
        self.template_value['navbar'] = {'booctools': True}


class AnalyticsHandler(TableRenderingHandler):
    class NavForm(wtf.Form):
        query = wtf.RadioField('Analytics query',
                choices=[(k, k) for k in analytics_queries.keys()],
                id='AHquery')
        view = wtf.RadioField('View',
                choices=[('csv', 'csv'), ('table', 'table'), ('debug', 'debug')],
                id='AHview',
                default='table')
        unit = wtf.IntegerField('Unit Number (for unit queries)',
                [wtf.validators.Optional()],
                id='AHunit')
        student = wtf.StringField('Student email (for edit history query)',
                [wtf.validators.Optional()],
                id='AHstudent')

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

    def render_choices_page(self, error=''):
        self.redirect('/long_analytics')


class JobsHandler(BaseHandler):
    def get(self):
        if not Roles.is_course_admin(self.app_context):
            self.abort(403)
        from modules.csv import jobs
        job = jobs.the_job()
        deferred.defer(job.run)

class TestMapBlah(TableMakerMapper):
    KIND = Student
    FIELDS = ['good', 'bad']

    def map(self, student):
        self.add_row({'good': 7, 'bad': 4})

class BadgeAssertionMapQuery(TableMakerMapper):
    FIELDS = [
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
    KIND = badge_models.BadgeAssertion

    FILTERS = [('revoked', False)]

    def __init__(self, **kwargs):
        super(BadgeAssertionMapQuery, self).__init__()
        self.course = kwargs['course']

    def map(self, ass):
        d = {}
        for f in ['issuedOn', 'expires', 'revoked', 'evidence']:
            d[f] = getattr(ass, f)

        d['badge_name'] = ass.badge_name
        student = ass.recipient
        d['recipient'] = student.badge_name
        d['email'] = student.key().name()
        d['group_id'] = student.group_id
        d['id'] = ass.key().id()
        logging.warning('Considering %s issued to %s', d['badge_name'], d['email'])

        if not ass.badge_name.startswith('expert'):
            part_num = get_part_num_by_badge_name(ass.badge_name)
            report = PartReport.on(student, self.course, part_num)
            unit_reps = report.unit_reports
            for attr in ['endorsements', 'promotions', 'comments']:
                d[attr] = sum(getattr(u, attr) for u in unit_reps)

        self.add_row(d)

class BadgeAssertionMapQueryWithRevoked(BadgeAssertionMapQuery):
    FILTERS = []

class TermPaperQuery(TableMakerMapper):
    _term_paper_unit_number = 12
    _link_template = Markup('<a href="%s">link</a>')
    KIND = WikiPage
    FILTERS = [('unit', _term_paper_unit_number)]
    FIELDS = [
            'email',
            'paper_link',
            'badge_issued',
            'badge_edit_link',
            ]

    def __init__(self, **kwargs):
        self.course = kwargs['course']
        self.unit = kwargs['unit']
        self.host_url = kwargs['host_url']
        super(TermPaperQuery, self).__init__()

    def map(self, wiki_page):
        row = {
                'email': wiki_page.author_email,
                'paper_link': self._link_template % (
                    self.host_url + '/' + wiki_page.link),
                'badge_edit_link': self._link_template % (
                    self.host_url + '/badges/custom?' + urllib.urlencode({'email': wiki_page.author_email})),
                }

        badge_assertions = badge_models.BadgeAssertion.all().filter('recipient', wiki_page.author)
        badge_assertions.filter('revoked', False)
        any_paper_assertions = any(
                [self._term_paper_slug_matcher(ass.badge_name) for ass in badge_assertions])
        row['badge_issued'] = any_paper_assertions
        self.add_row(row)

    def _term_paper_slug_matcher(self, s):
        return s.startswith('paper')



def wordcount_zeros():
    return [0] * 13
class WikifolioWordCountQuery(TableMakerMapper):
    KIND = WikiPage
    FIELDS = [
            'name',
            'email',
            'profile',
            'unit1',
            'unit2',
            'unit3',
            'unit4',
            'unit5',
            'unit6',
            'unit7',
            'unit8',
            'unit9',
            'unit10',
            'unit11',
            'unit12',
            ]


    def __init__(self, **kwargs):
        TableMakerMapper.__init__(self, **kwargs)
        self.counts = defaultdict(wordcount_zeros)
        self.names = {}

    _re_word_boundaries = re.compile(r'\b')
    def num_words(self, string):
        return len(self._re_word_boundaries.findall(string)) >> 1

    def map(self, page):
        email = page.author_email
        if email not in self.names:
            if page.author:
                self.names[email] = page.author.name

        # Switch None (indicating the profile page) to 0 (for array index)
        unit = page.unit or 0

        count = 0
        for pname in page.dynamic_properties():
            text = getattr(page, pname)
            if text:
                count += self.num_words(
                        Markup(text).striptags())

        self.counts[email][unit] = count

    def finish(self):
        for email,counts in self.counts.iteritems():
            row = [
                    self.names.get(email, ''),
                    email,
                    ] + counts
            self.add_row(dict(zip(self.FIELDS, row)))


class CommentCountQuery(TableMakerMapper):
    KIND = WikiComment
    FIELDS = [ 'c%d' % n for n in range(40) ]

    def __init__(self, **kwargs):
        TableMakerMapper.__init__(self)
        self.tab = CrossTab()
        self.word_tab = CrossTab()
        self.names = {}

    _re_word_boundaries = re.compile(r'\b')
    def num_words(self, string):
        return len(self._re_word_boundaries.findall(string)) >> 1


    def map(self, comment):
        email = comment.author_email
        if email not in self.names:
            self.names[email] = comment.author.name
        unit = comment.topic.unit
        if unit is None:
            unit = 'Profile'
        self.tab.add(email=email, comments_in_unit=unit)
        comment_text = Markup(comment.text).striptags()
        self.word_tab.add_count(
                self.num_words(comment_text),
                email=email, words_in_unit=unit)
        return ([], [])

    def finish(self):
        for comments_row, words_row in itertools.izip(
                self.tab.table('email', 'comments_in_unit'),
                self.word_tab.table('email', 'words_in_unit')):
            blank_or_email = comments_row[0]

            if ':' in blank_or_email:
                blank_or_email = blank_or_email.split(':', 1)[1]

            name = self.names.get(blank_or_email, '')

            row = [name, blank_or_email]
            for comment_cell, word_cell in zip(
                    comments_row[1:], words_row[1:]):
                row.extend([comment_cell, word_cell])

            self.add_row(dict(zip(self.FIELDS, row)))


class PromotionQuery(TableMakerMapper):
    KIND = Student
    FIELDS = [
            'name',
            'email',
            ]
    for u in range(1,13):
        FIELDS.append('u%d promoted' % u)
        FIELDS.append('u%d promoted email' % u)
        FIELDS.append('u%d text' % u)

    def __init__(self, **kwargs):
        self._names = {}
        TableMakerMapper.__init__(self)

    def name(self, email):
        name = self._names.get(email, None)
        if name:
            return name
        else:
            stud = Student.get_by_email(email)
            self._names[email] = stud.name
            return stud.name

    def map(self, student):
        row = {
                'name': student.name,
                'email': student.key().name()
                }

        self._names[student.key().name()] = student.name

        promos = Annotation.exemplaries(who=student).fetch(limit=30)
        promos = sorted(promos, key=lambda p: p.unit)

        for promo in promos:
            u = promo.unit or promo.what.unit
            email = promo.whose_email
            row['u%d promoted email' % u] = email
            row['u%d promoted' % u] = self.name(email)
            row['u%d text' % u] = promo.reason
        self.add_row(row)


class UnitCommentQuery(TableMakerMapper):
    FIELDS = [
            'orig_row_number',
            'link',
            'unit',
            'page_author',
            'comment_author',
            'comment_author_has_posted',
            'is_reply',
            'added_time',
            'is_edited',
            'is_deleted',
            'text',
            ]
    KIND = WikiPage

    def __init__(self, **kwargs):
        self.course = kwargs['course']
        self.unit = kwargs['unit']
        self.host_url = kwargs['host_url']
        if not self.unit:
            raise ValueError('"unit" parameter is required for this query')
        self.counter = itertools.count(1)
        self.FILTERS = [('unit', self.unit)]
        self._has_posted = dict()
        super(UnitCommentQuery, self).__init__()

    def has_posted(self, student):
        email = student.key().name()
        if email not in self._has_posted:
            self._has_posted[email] = bool(
                    db.get(WikiPage.get_key(student, unit=self.unit)))
        return self._has_posted[email]

    def map(self, page):
        # May want to re-introduce the prefetcher, but want it to last per-batch.
        # Maybe write a .__getstate__(self) method, that deletes it from the __dict__
        # before this mapper gets pickled.
        #prefetcher = prefetch.CachingPrefetcher()
        comments = page.comments.run(limit=100)
        if not page.author:
            return
        page_author = "%s (%s)" % (page.author.name, page.author_email)
        #prefetcher.add(page.author)

        #for comment in wf.sort_comments(prefetcher.prefetch(comments, WikiComment.author)):
        for comment in wf.sort_comments(list(comments)):
            row = defaultdict(str)
            row['orig_row_number'] = next(self.counter)
            row['page_author'] = page_author
            row['link'] = self.host_url + '/' + wf.comment_permalink(comment)
            row['comment_author'] = "%s (%s)" % (comment.author.name, comment.author_email)
            row['comment_author_has_posted'] = self.has_posted(comment.author)
            row['unit'] = page.unit
            row['is_reply'] = comment.is_reply()
            for attr in ['added_time', 'text']:
                row[attr] = getattr(comment, attr)
            for attr in ['is_edited', 'is_deleted']:
                row[attr] = bool(getattr(comment, attr))
            row['text'] = re.sub(r'<[^>]*?>', '', row['text'])
            self.add_row(row)

mapper_queries = OrderedDict()
mapper_queries['badge_assertions'] = BadgeAssertionMapQuery
mapper_queries['badge_assertions_with_revoked'] = BadgeAssertionMapQueryWithRevoked
mapper_queries['unit_all_comments'] = UnitCommentQuery
mapper_queries['promotions'] = PromotionQuery
mapper_queries['term_paper'] = TermPaperQuery
mapper_queries['comments_made_per_unit'] = CommentCountQuery
mapper_queries['wikifolio_word_counts'] = WikifolioWordCountQuery
mapper_queries['fixed_unit_ranking_query'] = FixedUnitRankingQuery


class EditDistanceQuery(TableMakerMapper):
    KIND = Student
    FILTERS = [('is_participant', True)]
    FIELDS = [
            'name',
            'email',
            'wiki_id',
            'words2',
            'diff2.3',
            'words3',
            'diff3.4',
            'words4',
            'diff4.5',
            'words5',
            'diff5.6',
            'words6',
            'diff6.7',
            'words7',
            'diff7.8',
            'words8',
            'diff8.9',
            'words9',
            'diff9.10',
            'words10',
            'diff10.11',
            'words11',
            ]

    def __init__(self, **kwargs):
        #for k in kwargs:
            #setattr(self, k, kwargs[k])
        super(EditDistanceQuery, self).__init__()

    def map(self, student):
        row = {
                'name': student.name,
                'email': student.key().name(),
                'wiki_id': student.wiki_id,
                }
        page_keys = [
                WikiPage.get_key(student, unit)
                for unit in range(2, 12)
                ]
        pages = sorted(db.get(page_keys), key=lambda p: getattr(p, 'unit', 999999))

        last_context = None
        this_context = None
        for page in pages:
            if not page:
                break
            this_context = self.tokenize(page.context or '')
            row['words%d' % page.unit] = len(this_context)

            if last_context is not None:
                diff = edit_distance.levenshtein(last_context, this_context)
                row[self._label(page.unit)] = diff

            last_context = this_context

        self.add_row(row)

    def tokenize(self, string):
        return re.split(r'\W+', Markup(string).striptags())

    def _label(self, this_unit):
        last_unit = this_unit - 1
        return "diff%d.%d" % (last_unit, this_unit)

mapper_queries['context_edit_distance'] = EditDistanceQuery


class MapperTableHandler(TableRenderingHandler, ReflectiveRequestHandler):
    TITLE = 'HIIIII'
    default_action = 'prep'
    get_actions = ['prep', 'watch', 'download', 'view']
    post_actions = ['start']

    class NavForm(wtf.Form):
        query = wtf.RadioField('Analytics query',
                choices=[(k, k) for k in mapper_queries.keys()],
                id='MTquery')
        unit = wtf.IntegerField('Unit Number (for unit queries)',
                validators=[wtf.validators.Optional()],
                id='MTunit')

    def _action_url(self, action, **kwargs):
        params = dict(kwargs)
        params['action'] = action
        return '?'.join((
            self.request.path,
            urllib.urlencode(params)))

    def get_prep(self):
        if not Roles.is_course_admin(self.app_context):
            self.abort(403)
        self.render_form(self.NavForm())

    def render_form(self, form):
        self.prettify()
        self.template_value['form'] = form
        self.template_value['xsrf_token'] = self.create_xsrf_token('start')
        self.template_value['action_url'] = self._action_url('start')
        self.template_value['title'] = self.TITLE

        self.template_value['classic_form'] = AnalyticsHandler.NavForm()
        self.template_value['classic_action_url'] = '/analytics'
        self.render('csv_form.html')

    def post_start(self):
        if not Roles.is_course_admin(self.app_context):
            self.abort(403)

        form = self.NavForm(self.request.POST)
        if not form.validate():
            self.render_form(form)
            return

        query_class = mapper_queries[form.query.data]
        mapper = query_class(course=self.get_course(), unit=form.unit.data, host_url=self.request.host_url)
        assert isinstance(mapper, TableMakerMapper)
        job_id = mapper.job_id
        deferred.defer(mapper.run, batch_size=50)
        self.redirect(self._action_url('watch', job_id=job_id))
        
    def get_watch(self):
        if not Roles.is_course_admin(self.app_context):
            self.abort(403)

        job_id = self.request.GET.get('job_id', None)
        if not job_id:
            self.abort(404)

        self.prettify()
        result = TableMakerResult(job_id)
        self.template_value['result'] = result
        is_finished = result.is_finished

        continue_links = {}
        if is_finished:
            continue_links['Download as CSV'] = self._action_url('download', job_id=job_id)
            continue_links['View as table'] = self._action_url('view', job_id=job_id)
        self.template_value['continue_links'] = continue_links

        self.template_value['title'] = self.TITLE
        self.template_value['problems'] = []
        self.render('csv_watch.html')

    def get_download(self):
        if not Roles.is_course_admin(self.app_context):
            self.abort(403)

        job_id = self.request.GET.get('job_id', None)
        if not job_id:
            self.abort(404)

        result = TableMakerResult(job_id)
        fields = result.fields
        self.render_as_csv(fields, result)

    def get_view(self):
        if not Roles.is_course_admin(self.app_context):
            self.abort(403)

        job_id = self.request.GET.get('job_id', None)
        if not job_id:
            self.abort(404)

        result = TableMakerResult(job_id)
        fields = result.fields
        self.render_as_table(fields, result)


module = None

def register_module():
    global module

    handlers = [
            ('/analytics', AnalyticsHandler),
            ('/long_analytics', MapperTableHandler),
            ('/adminjob', JobsHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Student CSV", "Student CSV",
            [], handlers)

    return module

