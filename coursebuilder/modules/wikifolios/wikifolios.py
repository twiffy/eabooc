"""
Wikifolios module for Google Course Builder
"""

from models import custom_modules, transforms
from models.config import ConfigProperty
from models.models import Student, EventEntity, MemcacheManager, AssessmentTracker
from models.roles import Roles
from common import ckeditor, prefetch
import bleach
import webapp2
import humanize
from controllers.utils import BaseHandler, ReflectiveRequestHandler, XsrfTokenManager
from modules.wikifolios.wiki_models import WikiPage, WikiComment, Annotation, Notification
from modules.regconf.regconf import FormSubmission
from google.appengine.api import users, mail
from google.appengine.ext import db, deferred
from modules.wikifolios import page_templates
from operator import attrgetter
import itertools, collections
import textwrap
import filters
import logging
import functools
import urllib
import wtforms as wtf
from jinja2 import Markup
from wiki_bleach import *

NO_OBJECT = {}

STUDENTS_CAN_DO_ASSIGNMENTS = ConfigProperty(
        'students_can_do_assignments', bool,
        """Whether to allow students to create and edit pages on their
        wikifolios, other than their profiles.""",
        True)

no_result = object()

class lazy_iter(object):
    def __init__(self, fn, *args, **kwargs):
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._result = no_result

    def __iter__(self):
        if self._result is no_result:
            self._result = self._fn(*self._args, **self._kwargs)
        return iter(self._result)

def get_student_by_wiki_id(wiki_id):
    return Student.get_enrolled_student_by_wiki_id(wiki_id)

def student_profile_link(wiki_id):
    return "wikiprofile?" + urllib.urlencode({'student': wiki_id})

def comment_permalink(comment):
    return 'wikicomment?' + urllib.urlencode({
        'action': 'permalink',
        'comment_id': comment.key().id(),
        })

def update_wikis_posted(student_key, unit, is_draft):
    unit = int(unit)
    student = db.get(student_key)
    if unit not in student.wikis_posted:
        student.wikis_posted.append(unit)
    if is_draft:
        student.wikis_posted.remove(unit)
    student.put()

def notify_other_people_in_thread(parent, new, exclude=[]):
    def author(comment):
        return WikiComment.author.get_value_for_datastore(comment)
    new_author = author(new)
    new_author_name = new.author.name
    exclude_authors = set(a.key() for a in exclude)

    to_put = []

    if author(parent) not in exclude_authors:
        exclude_authors.add(author(parent))
        note = Notification(
                recipient=author(parent),
                url=comment_permalink(new),
                text=unicode(Markup('<b>%(commenter)s</b> replied to your comment.') % ({
                    'commenter': new_author_name,
                    })))
        to_put.append(note)

    for comment in parent.replies:
        if author(comment) not in exclude_authors:
            exclude_authors.add(author(comment))
            note = Notification(
                    recipient=author(comment),
                    url=comment_permalink(new),
                    text=unicode(Markup('<b>%(commenter)s</b> also replied to a comment.') % ({
                        'commenter': new_author_name,
                        })))
            to_put.append(note)

    return db.put(to_put)

def sort_comments(comments):
    """
    Sort comments so that they are in the order:
    parent
      reply-1
      reply-2.

    This is a flat list, the template notices whether they are replies at a later point.
    """
    first_sort = sorted(comments, key=attrgetter('added_time'))
    def final_sort_key(comment):
        if comment.parent_added_time:
            return comment.parent_added_time
        if comment.is_reply():
            logging.warning("comment has parent_comment but no parent_added_time, this shouldn't happen")
        return comment.added_time
    return sorted(first_sort, key=final_sort_key)

class WikiBaseHandler(BaseHandler):
    # I don't like how leaky this is, always having to check for the None return.
    def personalize_page_and_get_wiki_user(self):
        user = self.personalize_page_and_get_enrolled()
        self.template_value['navbar'] = {'wiki': True}
        self.template_value['content'] = ''
        if Roles.is_course_admin(self.app_context):
            self.template_value['student_link'] = filters.student_link_for_admins
        else:
            self.template_value['student_link'] = filters.student_link
        if users.is_current_user_admin():
            self.template_value['dark_magic_db_edit_href'] = filters.dark_magic_db_edit_href
        self.template_value['comment_permalink'] = comment_permalink
        self.template_value['humanize'] = humanize
        if hasattr(self, 'create_xsrf_token'):
            # TODO: refactor to split more complicated pages out from the profile list handler
            self.template_value['create_xsrf_token'] = self.create_xsrf_token
        self.template_value['can_do_assignments'] = STUDENTS_CAN_DO_ASSIGNMENTS.value
        self.template_value['user_can_edit_comment'] = functools.partial(
                self._user_can_edit_comment, user)
        if not user or not self.assert_participant_or_fail(user):
            return
        return user

    def show_notifications(self, current_student):
        notes = current_student.notification_set.filter('seen', False).run(limit=20)
        self.template_value['notifications'] = sorted(notes,
                key=Notification.sort_key_func,
                reverse=True)

    def _editor_role(self, query, current_student, template=True):
        if not (query and current_student):
            return None
        if current_student:
            assert current_student.key().name() == users.get_current_user().email()
        is_author = (current_student
                and current_student.wiki_id == query['student']
                and current_student.is_enrolled)
        role = None
        if is_author:
            role = 'author'
        elif Roles.is_course_admin(self.app_context):
            role = 'admin'
        if template:
            self.template_value['editor_role'] = role
            if role != 'author':
                self.template_value['navbar'] = {'participants': True}
        return role

    def assert_editor_role(self, *args, **kwargs):
        role = self._editor_role(*args, **kwargs)
        if not role:
            logging.warning("Denying edit, no editor role.")
            logging.info("%s", repr(args))
            self.abort(403, "You cannot edit this page.")
        return role

    def _can_view(self, query, current_student):
        if current_student:
            assert current_student.key().name() == users.get_current_user().email()
        is_enrolled = (current_student and current_student.is_enrolled)
        return is_enrolled or Roles.is_course_admin(self.app_context)

    def _user_can_edit_comment(self, user, comment):
        # would be great to use the same code as _editor_role above...
        author_id = str(WikiComment.author.get_value_for_datastore(comment))
        return str(user.key()) == author_id or Roles.is_course_admin(self.app_context)

    def _can_comment(self, query, current_student):
        return self._can_view(query, current_student)

    def _create_action_url(self, query, action="view"):
        params = dict(query)
        params.update({
                'action': action,
                })
        return '?'.join((
                self.request.path,
                urllib.urlencode(params)))

    def show_comments(self, page):
        the_comments = WikiComment.comments_on_page(page)
        #the_comments = lazy_iter(sort_comments, the_comments)
        the_comments = sort_comments(the_comments)
        self.template_value['comments'] = the_comments

    def post_comment(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)

        if not query:
            self.abort(404)

        parent = None
        try:
            parent_id = int(self.request.get('parent', ''))
            parent = WikiComment.get_by_id(parent_id)
        except:
            pass


        if not self._can_comment(query, user):
            logging.warning("Attempt to comment illegally")
            self.abort(403, "You are not allowed to comment on this page.")

        page = self._find_page(query)
        if not page:
            self.abort(404)



        # TODO: use wtforms for comments
        comment = WikiComment(
                author=user,
                topic=page,
                parent_comment=parent,
                text=bleach_comment(self.request.get('text', '')))
        comment.put()

        EventEntity.record(
                'wiki-comment', users.get_current_user(), transforms.dumps({
                    'page-author': page.author.key().name(),
                    'page': str(page.key()),
                    'unit': page.unit,
                    'commenter': user.key().name(),
                    'text': comment.text,
                    'unbleached-text': self.request.get('text', ''),
                    'parent-comment': parent.key().id() if parent else None,
                    }))

        if query['student'] != user.wiki_id:
            descr = self.describe_query(query, page.author)
            note = Notification(
                    recipient=page.author,
                    url=comment_permalink(comment),
                    text=unicode(Markup('<b>%(commenter)s</b> commented on %(what)s.') % ({
                        'commenter': user.name,
                        'what': descr,
                        })))
            db.put(note)

        if parent:
            notify_other_people_in_thread(parent, comment,
                    exclude=[page.author, comment.author])

        self.redirect(self._create_action_url(query, 'view')
                + '#comment-%d' % comment.key().id())

    def post_flag(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)

        if not query:
            self.abort(404)

        if not self._can_view(query, user):
            logging.warning("Attempt to flag a page they can't see????")
            self.abort(403, "You are not allowed to do that.")

        page = self._find_page(query)
        if not page:
            self.abort(404)

        raw_reason = self.request.get('reason', '')
        reason = bleach_comment(raw_reason[:2000]) # limit size, de-fang

        Annotation.flag(
                page,
                user,
                reason)

        url = self.request.host_url + self._create_action_url(query, 'view')
        flagger_id = '%s <%s>' % (user.name, user.key().name())
        mail.send_mail_to_admins('BOOC Admin <booc.class@gmail.com>',
                'Inappropriate content reported',
                textwrap.dedent('''\
                The user %(flagger_id)s reported inappropriate content on this page:

                %(url)s

                Their comment was:

                %(reason)s
                ''' % {
                    'flagger_id': flagger_id,
                    'url': url,
                    'reason': reason,
                    }),
                reply_to=flagger_id)

        self.template_value['content'] = '''
            <div class="gcb-aside">
            <h1>Thank you for your report.</h1>
            It has been sent to the
            course administrators for review.
            </div>
            '''
        self.render('bare.html')

class WikiCommentHandler(WikiBaseHandler, ReflectiveRequestHandler):
    default_action = 'edit'
    get_actions = ['edit', 'delete', 'permalink']
    post_actions = ['save', 'delete']

    class _NavForm(wtf.Form):
        comment_id = wtf.IntegerField('Comment ID', [wtf.validators.Required()])

    def _find_comment(self):
        form = self._NavForm(self.request.GET)
        if not form.validate():
            self.abort(404)

        comment = WikiComment.get_by_id(form.comment_id.data)
        if not comment:
            self.abort(404, "The requested comment could not be found.")

        return comment

    def get_edit(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        comment = self._find_comment()
        if comment.is_deleted:
            self.template_value['content'] = 'You cannot edit a deleted comment'
            self.render('bare.html')
            return

        query = {
                'student': comment.author.wiki_id,
                'comment_id': comment.key().id(),
                }
        self.assert_editor_role(query, user)

        self.template_value['ckeditor_allowed_content'] = (
                ckeditor.allowed_content(COMMENT_TAGS,
                    COMMENT_ATTRIBUTES, COMMENT_STYLES))

        self.template_value['author'] = comment.author
        self.template_value['author_name'] = comment.author.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])
        self.template_value['content'] = comment.text
        self.template_value['action_url'] = functools.partial(
                self._create_action_url, query)
        self.render("wf_comment_edit.html")

    def get_permalink(self):
        comment = self._find_comment()
        root = comment.topic.link
        anchor = '#comment-%d' % comment.key().id()
        return self.redirect(root + anchor)

    def post_save(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        comment = self._find_comment()
        if comment.is_deleted:
            self.template_value['content'] = 'You cannot edit a deleted comment'
            self.render('bare.html')
            return

        query = {
                'student': comment.author.wiki_id,
                'comment_id': comment.key().id(),
                }
        self.assert_editor_role(query, user)

        old_text = comment.text
        comment.text = bleach_comment(self.request.get('text', ''))
        comment.is_edited = True
        comment.editor = user
        comment.put()

        EventEntity.record(
                'wiki-comment-edit', users.get_current_user(), transforms.dumps({
                    'comment-author': comment.author.key().name(),
                    'comment': str(comment.key()),
                    'editor': user.key().name(),
                    'text': comment.text,
                    'old-text': old_text,
                    'unbleached-text': self.request.get('text', ''),
                    }))

        self.redirect(comment.topic.link)

    def get_delete(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        comment = self._find_comment()

        query = {
                'student': comment.author.wiki_id,
                'comment_id': comment.key().id(),
                }
        self.assert_editor_role(query, user)

        self.template_value['author_name'] = comment.author.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])
        self.template_value['content'] = comment.text
        self.template_value['action_url'] = functools.partial(
                self._create_action_url, query)
        self.render("wf_comment_delete.html")

    def post_delete(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        comment = self._find_comment()

        query = {
                'student': comment.author.wiki_id,
                'comment_id': comment.key().id(),
                }
        self.assert_editor_role(query, user)

        EventEntity.record(
                'wiki-comment-delete', users.get_current_user(), transforms.dumps({
                    'comment-author': comment.author.key().name(),
                    'comment': str(comment.key()),
                    'editor': user.key().name(),
                    'text': comment.text,
                    }))

        comment.is_deleted = True
        comment.is_edited = True
        comment.editor = user
        comment.put()
        self.redirect(comment.topic.link)


class WikiPageHandler(WikiBaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = ["view", "edit"]
    post_actions = ["save", "comment", "endorse", "flag", "exemplary", 'incomplete']

    class _NavForm(wtf.Form):
        unit = wtf.IntegerField('Unit number', [
            wtf.validators.NumberRange(min=1, max=100),
            ])
        student = wtf.IntegerField('Student id', [
            wtf.validators.Optional(),
            wtf.validators.NumberRange(min=1, max=100000000000),
            ])

    def describe_query(self, query, user):
        "Describes the query to a particular user"
        if query['student'] == user.wiki_id:
            whose = "your "
        else:
            whose = Markup("<b>%s</b>'s ") % get_student_by_wiki_id(query['student']).name

        what = Markup("unit %s wikifolio page") % query['unit']
        return whose + what


    def _get_query(self, user):
        form = self._NavForm(self.request.params)
        data = None
        if form.validate():
            data = form.data
        else:
            # TODO maybe log why it's not good
            logging.warning("Denied query, it did not validate.")
            logging.info("%s", repr(self.request.params))
            self.template_value['content'] = 'Sorry, that page was not found.'
            self.error(403)
            data = None

        if data and not data['student'] and user:
            data['student'] = user.wiki_id

        self.template_value['action_url'] = functools.partial(
                self._create_action_url, data)
        return data

    def _find_page(self, query, create=False, student_model=None):
        logging.info(query)
        assert query
        # TODO don't have to do this query if it's your own page,
        # optimize this.  Also, cache.
        # TODO maybe store the wiki_id of the student in the Page,
        # and look up by that, so we don't fetch the Student
        # model twice (once by wiki id, once as a reference in
        # the page)
        if not student_model:
            student_model = get_student_by_wiki_id(query['student'])
        if not student_model:
            return None

        key = WikiPage.get_key(student_model, query['unit'])
        if not key:
            # Not only is there no page,
            # but the request is invalid too.
            return None

        page = WikiPage.get(key)
        if (not page) and create:
            page = WikiPage(key=key)

        return page

    def show_unit(self, query):
        self.template_value['unit'] = self.find_unit_by_id(query['unit'])

    def show_all_endorsements(self, page):
        self.template_value['endorsements'] = prefetch.prefetch_refprops(
                Annotation.endorsements(page), Annotation.who)

        self.template_value['exemplaries'] = prefetch.prefetch_refprops(
                Annotation.exemplaries(page), Annotation.who)

    def get_view(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)

        if not query:
            self.abort(404)
        elif not self._can_view(query, user):
            # They may have already bounced off the login page
            # from personalize_page_etc above
            self.abort(403)
        editor_role = self._editor_role(query, user)
        self.show_unit(query)
        if user.wiki_id == query['student']:
            author = user
        else:
            author = get_student_by_wiki_id(query['student'])
        self.template_value['author'] = author

        page = self._find_page(query, student_model=author)
        if page:
            prefetcher = prefetch.CachingPrefetcher(page.key(),
                    [author, user])

            self.template_value['fields'] = page_templates.viewable_model(page)
            self.template_value['is_draft'] = page.is_draft

            self.show_notifications(user)
            #self.show_comments(page)
            # Start comments loading async
            #comments = page.comments.run(limit=1000)
            endorsements = Annotation.endorsements(page).run(limit=50)
            exemplaries = Annotation.exemplaries(page).run(limit=50)
            self.template_value['incompletes'] = Annotation.incompletes(page).run(limit=50)

            comments = WikiComment.comments_on_page(page)

            if self._can_comment(query, user):
                self.template_value['can_comment'] = True
                self.template_value['ckeditor_comment_content'] = (
                        ckeditor.allowed_content(COMMENT_TAGS,
                            COMMENT_ATTRIBUTES, COMMENT_STYLES))

            if Roles.is_course_admin(self.app_context):
                self.template_value['can_mark_incomplete'] = True

            endorsements = prefetcher.prefetch(endorsements,
                    Annotation.who)
            self.template_value['endorsements'] = endorsements

            exemplaries = prefetcher.prefetch(exemplaries,
                    Annotation.who)
            self.template_value['exemplaries'] = exemplaries

            self.template_value['comments'] = sort_comments(prefetcher.prefetch(comments, WikiComment.author))
            prefetcher.done()

            if query['unit'] == 12:
                self.template_value['review'] = Annotation.reviews(what=page).get()

            def who(ann):
                return Annotation.who.get_value_for_datastore(ann)

            if query['student'] == user.wiki_id:
                self.template_value['is_author'] = True
                self.template_value['endorsement_view'] = 'author'
                self.template_value['exemplary_view'] = 'author'
            else:
                if user.key() in [who(e) for e in endorsements]:
                    self.template_value['endorsement_view'] = 'has_endorsed'
                else:
                    self.template_value['endorsement_view'] = 'can_endorse'

                if user.key() in [who(e) for e in exemplaries]:
                    self.template_value['exemplary_view'] = 'has_exemplaried'
                else:
                    self.template_value['exemplary_view'] = 'can_exemplary'

            self.render(page_templates.templates[query['unit']])
        else:
            self.template_value['fields'] = {}
            if not editor_role:
                self.template_value['alert'] = "This user has not created this wikifolio page yet!"
            self.error(200)
            self.render(page_templates.templates[query['unit']])

    def post_incomplete(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        if not Roles.is_course_admin(self.app_context):
            self.abort(403)
        query = self._get_query(user)
        if not query:
            logging.warning("Query was broken")
            self.abort(404)

        page = self._find_page(query)
        if not page:
            self.abort(404)

        if 'mark' in self.request.POST:
            Annotation.incomplete(
                    page, user, self.request.POST['reason'])
            EventEntity.record(
                    'admin-mark-incomplete', users.get_current_user(), transforms.dumps({
                        'page-author': page.author.key().name(),
                        'page': str(page.key()),
                        'reason': self.request.POST['reason'],
                        }))
        elif 'undo' in self.request.POST:
            EventEntity.record(
                    'admin-undo-mark-incomplete', users.get_current_user(), transforms.dumps({
                        'page-author': page.author.key().name(),
                        'page': str(page.key()),
                        'reason': self.request.POST.get('reason', '(none)'),
                        }))
            db.delete(Annotation.incompletes(page).fetch(limit=100))
        self.redirect(self._create_action_url(query, 'view'))


    def post_exemplary(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)
        if not query:
            logging.warning("Query was broken")
            self.abort(404)
        content = ''

        if not self._can_view(query, user):
            logging.warning("Not allowed to view")
            self.abort(403)
        elif user.wiki_id == query['student']:
            logging.warning("Attempt to mark own page as exemplary")
            self.abort(403, "You are not allowed to mark your own page exemplary.")

        page = self._find_page(query)

        previous_exemplary = Annotation.exemplaries(page, user).get()

        if previous_exemplary:
            if 'undo' in self.request.POST:
                logging.info("Undoing an exemplary")
                previous_exemplary.delete()
                self.redirect(self._create_action_url(query, 'view'))
                return
            logging.warning("Attempt to mark exemplary multiple times.")
            self.redirect(self._create_action_url(query, 'view'))
            return

        reason = bleach_comment(self.request.get('comment'))
        if len(reason) < 10 or len(reason) > 450:
            self.template_value['content'] = '''
            <div class="gcb-aside">
              You have to give a reason for marking something exemplary.  The
              reason must be between 10 and 450 letters in length (yours was
              %d).  Please use your Back button and try again!
            </div>
            ''' % len(reason)
            self.render('bare.html')
            return

        Annotation.exemplary(page, user, reason)

        self.redirect(self._create_action_url(query, 'view'))

    def post_endorse(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)
        if not query:
            self.abort(404)
        content = ''

        if not self._can_view(query, user):
            self.abort(403)
        elif user.wiki_id == query['student']:
            logging.warning("Attempt to mark own page as complete")
            self.abort(403, "You are not allowed to mark your own page complete.")

        page = self._find_page(query)
        existing_endorsement = Annotation.endorsements(page, user).get()
        if 'undo' in self.request.POST:
            if existing_endorsement:
                existing_endorsement.delete()
                EventEntity.record(
                        'wiki-endorse-delete', users.get_current_user(),
                        transforms.dumps({
                            'endorsed-page': str(page.key())
                            }))
        else:
            if existing_endorsement:
                logging.warning("Attempt to mark complete multiple times.")
                self.abort(403, "You've already marked this page complete.")
            Annotation.endorse(page, user, 'all_done' in self.request.POST)
            EventEntity.record(
                    'wiki-endorse', users.get_current_user(),
                    transforms.dumps({
                        'all_done': 'all_done' in self.request.POST,
                        'endorsed-page': str(page.key())
                        }))

        self.redirect(self._create_action_url(query, 'view'))

    def get_edit(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)
        self.template_value['ckeditor_allowed_content'] = (
                ckeditor.allowed_content(ALLOWED_TAGS,
                    ALLOWED_ATTRIBUTES, ALLOWED_STYLES))

        if not query:
            self.abort(404)

        self.assert_editor_role(query, user)

        # We call with create=True to eliminate a conditional on how
        # to set the author_name later.  But we don't .put() it.
        page = self._find_page(query, create=True)

        self.show_unit(query)
        self.show_comments(page)
        self.show_all_endorsements(page)

        form_init = page_templates.forms[query['unit']]
        self.template_value['fields'] = form_init(None, page)

        self.template_value['author'] = page.author
        self.template_value['is_draft'] = page.is_draft if page.is_saved() else True
        self.template_value['editing'] = True
        self.render(page_templates.templates[query['unit']])

    def get_unit(self, unit_id):
        # TODO find_unit_by_id??
        unit_id = unicode(unit_id) # harrumph
        units = self.get_units()
        for unit in units:
            if unit.unit_id == unit_id:
                return unit

    def post_save(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query(user)

        self.assert_editor_role(query, user)
        if not STUDENTS_CAN_DO_ASSIGNMENTS.value:
            logging.warning("Assignments not yet open (STUDENTS_CAN_DO_ASSIGNMENTS is false)")
            content = "Assignments are not yet available."
            self.error(403)
            self.render("bare.html")
            return
        page = self._find_page(query, create=True)

        form_init = page_templates.forms[query['unit']]
        form = form_init(self.request.POST)
        if not form.validate():
            logging.warning("Denied post because form did not validate")
            logging.info("%s", repr(self.request.params))
            self.abort(403, 'Form did not validate.........')

        old_page = db.to_dict(page)
        # TODO fix
        del old_page['edited_timestamp']
        for k,v in form.data.items():
            if isinstance(v, basestring):
                setattr(page, k, db.Text(v))
            else:
                setattr(page, k, v)
        page.unit = query['unit']

        if page.author_email == user.key().name():
            page.group_id = user.group_id
        else:
            page.group_id = page.author.group_id

        is_draft = bool(self.request.POST.get('Draft', False))
        page.is_draft = is_draft
        page.put()
        EventEntity.record(
                'edit-wiki-page', users.get_current_user(), transforms.dumps({
                    'page-author': page.author_email,
                    'page-editor': user.key().name(),
                    'unit': page.unit,
                    'before': old_page,
                    'after': form.data,
                    'is_draft': is_draft,
                    }))

        deferred.defer(update_wikis_posted, page.author_key, page.unit, is_draft)

        self.redirect(self._create_action_url(query, 'view'))


class WikiProfileListHandler(WikiBaseHandler):
    group_names = {
                'administrator': 'Administrators',
                'educator': 'Educators (K-12)',
                'faculty': 'Faculty (Post-secondary)',
                'researcher': 'Researchers',
                'student': 'Students',
                'other': 'Other',

                # these are names, rather than values, of columns
                'is_teaching_assistant': 'Teaching Assistants',
                None: 'All Students',
                }
    # Gotta change None to 'all' or something... which means messing with conditionals lots
    allowed_groups = frozenset(('role', None, 'group_id', 'is_teaching_assistant'))
    default_group = None

    def group_name(self, db_val):
        return self.group_names.get(db_val, db_val)

    def get(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        self.template_value['navbar'] = {'participants': True}
        self.template_value['group_name'] = self.group_name

        group_by = self.request.get('group', None)
        if group_by not in self.allowed_groups:
            logging.debug('Not accepting requested grouping %s', group_by)
            group_by = self.default_group

        self.template_value['group_by'] = group_by

        projection = ['wiki_id', 'name', 'wikis_posted']

        # will need to cache this somehow.
        student_list = Student.all()
        student_list.filter('is_enrolled =', True)
        student_list.filter('is_participant =', True)
        # TODO refactor to switch & stuff???
        if group_by in ('role', 'group_id'):
            student_list.order(group_by)
            projection.append(group_by)
        elif group_by == 'is_teaching_assistant':
            student_list.filter('is_teaching_assistant =', True)
        student_list.order('name')

        # our course is capped at 500 students, so...
        FETCH_LIMIT=600

        all_students = student_list.run(
                limit=FETCH_LIMIT,
                projection=projection,
                )
        if group_by in ('role', 'group_id'):
            lazy_groups = itertools.groupby(all_students,
                    lambda student: getattr(student, group_by))
            self.template_value['groups'] = lazy_groups
        else:
            self.template_value['groups'] = [ (self.group_names[group_by], all_students) ]


        self.render("wf_list.html")


class WikiProfileHandler(WikiBaseHandler, ReflectiveRequestHandler):
    default_action = "view"
    get_actions = [
            "view",
            "edit",
            ]
    post_actions = [
            "save",
            "comment",
            "flag",
            ]

    class _NavForm(wtf.Form):
        student = wtf.IntegerField('Student id', [
            wtf.validators.Optional(),
            wtf.validators.NumberRange(min=1, max=100000000000),
            ])

    def _get_query(self, unused_user=None):
        # TODO: maybe do redirects to ?student= from here?
        form = self._NavForm(self.request.params)
        if form.validate():
            self.template_value['action_url'] = functools.partial(
                    self._create_action_url, form.data)
            return form.data
        else:
            self.abort(404, 'Sorry, there is no such student.')

    def _find_page(self, query, create=False, student_model=None):
        logging.info(query)
        assert query
        # TODO don't have to do this query if it's your own page,
        # optimize this.  Also, cache.
        # TODO maybe store the wiki_id of the student in the Page,
        # and look up by that, so we don't fetch the Student
        # model twice (once by wiki id, once as a reference in
        # the page)
        if not student_model:
            student_model = get_student_by_wiki_id(query['student'])
        if not student_model:
            return None

        key = WikiPage.get_key(student_model, unit=None)
        if not key:
            # Not only is there no page,
            # but the request is invalid too.
            return None

        page = WikiPage.get(key)
        if (not page) and create:
            page = WikiPage(key=key)

        return page

    def get_view(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query()
        if not query or not query['student']:
            self.abort(302, location="wikiprofile?" + urllib.urlencode({
                'student': user.wiki_id}))

        if self.request.GET.get('confirm', False):
            self.template_value['alert'] = '''<b>Congratulations!</b> You are
                officially registered. Welcome to the course.  Have a look around!'''

        if user.wiki_id == query['student']:
            author = user
        else:
            author = get_student_by_wiki_id(query['student'])
        self.template_value['author'] = author

        profile_page = self._find_page(query, student_model=author, create=True)
        if not profile_page:
            # e.g. there is no student by that ID.
            self.abort(404)

        prefetcher = prefetch.CachingPrefetcher(profile_page.key(),
                [author, user])

        pages = WikiPage.query_by_student(author).run(limit=100)
        endorsements = author.own_annotations.order('-timestamp').filter('why IN', ['endorse', 'exemplary']).run(limit=10)
        self.show_notifications(user)
        comments = WikiComment.comments_on_page(profile_page)

        self._ensure_curricular_aim(author, profile_page)
        self.template_value['fields'] = page_templates.viewable_model(profile_page)


        self.template_value['author_name'] = author.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])

        editor_role = self._editor_role(query, user)

        units = self.get_units()
        pages_by_unit_u = { unicode(p.unit): p for p in pages }
        for unit in units:
            if unit.unit_id in pages_by_unit_u:
                unit._wiki_exists = True
                unit._is_draft = pages_by_unit_u[unit.unit_id].is_draft
            unit._wiki_link = "wiki?" + urllib.urlencode({
                'student': author.wiki_id,
                'action': 'view',
                'unit': unit.unit_id,
                })

        self.template_value['units'] = units

        endorsements = prefetcher.prefetch(endorsements, Annotation.whose)
        unit_dict = {int(u.unit_id): u for u in units if u.unit_id.isdigit()}
        for e in endorsements:
            try:
                e._title = unit_dict[e.unit].title
            except:
                pass
        self.template_value['endorsements'] = endorsements

        if self._can_comment(query, user):
            self.template_value['can_comment'] = True
            self.template_value['ckeditor_comment_content'] = (
                    ckeditor.allowed_content(COMMENT_TAGS,
                        COMMENT_ATTRIBUTES, COMMENT_STYLES))

        self.template_value['comments'] = sort_comments(prefetcher.prefetch(comments, WikiComment.author))
        prefetcher.done()
        self.render(page_templates.templates['profile'])

    def _ensure_curricular_aim(self, student, page):
        if not hasattr(page, 'curricular_aim'):
            try:
                pre_assignment = (FormSubmission.all()
                    .filter('form_name', 'pre')
                    .filter('user', student.key())
                    .order('-submitted').get())
                page.curricular_aim = bleach_entry(
                        pre_assignment.curricular_aim)
            except:
                page.curricular_aim = "(no curricular aim found! database error?)"
                logging.warning("Couldn't find a pre assignment form for %s", student.key().name())

    def get_edit(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query()
        if not query['student']:
            self.redirect("wikiprofile?" + urllib.urlencode({
                'student': user.wiki_id}))
            return

        self.assert_editor_role(query, user)

        self.template_value['ckeditor_allowed_content'] = (
                ckeditor.allowed_content(ALLOWED_TAGS,
                    ALLOWED_ATTRIBUTES, ALLOWED_STYLES))


        profile_page = self._find_page(query, create=True)
        assert profile_page
        self._ensure_curricular_aim(profile_page.author, profile_page)
        student_model = profile_page.author

        self.template_value['editing'] = True
        self.template_value['author'] = student_model
        self.template_value['author_name'] = student_model.name
        self.template_value['author_link'] = student_profile_link(
                query['student'])

        form_init = page_templates.forms['profile']

        self.template_value['fields'] = form_init(None, profile_page)

        self.render(page_templates.templates['profile'])

    def post_save(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        query = self._get_query()
        if not query:
            self.abort(404)

        self.assert_editor_role(query, user)

        page = self._find_page(query, create=True)

        form_init = page_templates.forms['profile']
        form = form_init(self.request.POST)
        if not form.validate():
            self.abort(403, 'Form did not validate.........')

        old_page = db.to_dict(page)
        # TODO fix
        del old_page['edited_timestamp']
        for k,v in form.data.items():
            setattr(page, k, db.Text(v))
        page.put()
        EventEntity.record(
                'edit-wiki-profile', users.get_current_user(), transforms.dumps({
                    'page-author': page.author.key().name(),
                    'page-editor': user.key().name(),
                    'before': old_page,
                    'after': form.data,
                    }))
        self.redirect(self._create_action_url(query, 'view'))
        return

    def describe_query(self, query, user):
        "Describes the query to a particular user"
        if query['student'] == user.wiki_id:
            whose = "your "
        else:
            whose = Markup("<b>%s</b>'s ") % get_student_by_wiki_id(query['student']).name

        what = Markup("profile page")
        return whose + what

class WikiCommentStreamHandler(WikiBaseHandler):
    '''A list, for admins, of all comments.'''
    def get(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return
        if not Roles.is_course_admin(self.app_context):
            self.abort(403)

        latest_comments = WikiComment.all().order('-added_time').fetch(limit=100)

        latest_comments = prefetch.prefetch_refprops(latest_comments,
                WikiComment.author)

        self.template_value['comments'] = latest_comments

        self.render('wf_admin_comment_list.html')


class CommentListHandler(WikiBaseHandler):
    '''A list of your own comments.'''
    def get(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        latest_comments = WikiComment.all()
        latest_comments.filter('author', user)
        latest_comments.order('-added_time')
        latest_comments = prefetch.prefetch_refprops(latest_comments,
                WikiComment.author)

        self.template_value['comments'] = latest_comments

        self.render('wf_comment_list.html')


class EndorsementListHandler(WikiBaseHandler):
    '''A list of all your endorsements & exemplaries'''
    def get(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        endorsements = Annotation.all()
        endorsements.filter('why IN', ['exemplary', 'endorse'])
        endorsements.filter('who', user)
        endorsements.order('-timestamp')

        endorsements = prefetch.prefetch_refprops(endorsements,
                Annotation.whose)

        self.template_value['endorsements'] = endorsements
        self.render('wf_endorsement_list.html')


class WikiUpdateListHandler(WikiBaseHandler):
    def get(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        latest_updates = WikiPage.most_recent()

        #for up in latest_updates:
            #up['author'] = Student.get_enrolled_student_by_email(up.author_email)

        self.template_value['updates'] = latest_updates
        self.template_value['navbar'] = {'participants': True}
        self.template_value['unit'] = self.find_unit_by_id
        self.render('wf_update_list.html')

class ExamResetHandler(BaseHandler):
    def get(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return
        if not Roles.is_super_admin():
            self.abort(403, "no.")

        self.response.write(Markup('''
        <html><body>exam reset csv: (email,exam to reset)<br>
        like 'test@example.com,Practices'<br>
        <form action="/exam_reset" method="POST"><textarea name="group_csv"></textarea>
        <br><input type="hidden" name="xsrf_token" value="%(xsrf)s">
        <br><label><input type="checkbox" name="really"> really do it?</label>
        <br><input type="submit"></form>
        </body>
        </html>
        ''') % { 'xsrf': XsrfTokenManager.create_xsrf_token('exam_reset') })

    def post(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return
        if not Roles.is_super_admin():
            self.abort(403, "no.")

        if not self.assert_xsrf_token_or_fail(self.request, 'exam_reset'):
            return

        import unicodecsv as csv
        import StringIO

        reader = csv.reader(
                StringIO.StringIO(self.request.get('group_csv')),
                delimiter=",",
                )
        really = bool(self.request.get('really', False))
        self.response.write(Markup("Really do it? %s<br>") % str(really))
        for line in reader:
            student = Student.get_enrolled_student_by_email(line[0])

            if student:
                self.response.write(Markup('<span style="color: #060;"> . </span>'))
                if really:
                    AssessmentTracker.reset(student, line[1])
                    EventEntity.record(
                            'assessment-reset',
                            users.get_current_user(),
                            transforms.dumps({
                                'student-email': student.key().name(),
                                'assessment': line[1],
                                }))

            else:
                self.response.write(Markup("<br>Couldn't find student by email: %s<br>") % repr(line))


class HarrumphHandler(BaseHandler):
    def get(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return
        if not Roles.is_super_admin():
            self.abort(403, "no.")

        self.response.write(Markup('''
        <html><body>group_id csv: (email,group_id)<br><form action="/grump" method="POST"><textarea name="group_csv"></textarea>
        <br><input type="hidden" name="xsrf_token" value="%(xsrf)s">
        <br><label><input type="checkbox" name="really"> really do it?</label>
        <br><input type="submit"></form>
        </body>
        </html>
        ''') % { 'xsrf': XsrfTokenManager.create_xsrf_token('set_group_ids') })

    def post(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return
        if not Roles.is_super_admin():
            self.abort(403, "no.")

        if not self.assert_xsrf_token_or_fail(self.request, 'set_group_ids'):
            return

        import unicodecsv as csv
        import StringIO

        reader = csv.reader(
                StringIO.StringIO(self.request.get('group_csv')),
                delimiter=",",
                )
        really = bool(self.request.get('really', False))
        self.response.write(Markup("Really do it? %s<br>") % str(really))
        for line in reader:
            student = Student.get_enrolled_student_by_email(line[0])
            if student:
                self.response.write(Markup('<span style="color: #060;"> . </span>'))
                if really:
                    student.group_id = line[1]
                    student.put()
            else:
                self.response.write(Markup("<br>Couldn't find student by email: %s<br>") % repr(line))


class NotificationHandler(BaseHandler):
    def get(self):
        user = self.personalize_page_and_get_enrolled()
        if not user:
            return
        note_id = None
        try:
            note_id = int(self.request.GET.get('id', None))
        finally:
            pass

        if not note_id:
            self.redirect('/')
            return

        note = Notification.get_by_id(note_id)
        if not note:
            logging.info("No such note.")
            self.redirect('/')
            return

        note_recip_email = Notification.recipient.get_value_for_datastore(note).name()
        if note_recip_email != user.key().name():
            logging.warning("%s accessed %s's notification", user.key().name(), note_recip_email)
            self.redirect('/')
            return

        self.redirect(note.url.encode('utf-8'))
        note.seen = True
        note.put()


class NotificationListHandler(WikiBaseHandler):
    def get(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        notes = user.notification_set.run()
        notes = sorted(notes,
                key=Notification.sort_key_func,
                reverse=True)
        self.template_value['notifications'] = notes
        self.render('wf_all_notifications.html')


class ClassWikiHandler(WikiBaseHandler):
    resource_field_name = {
            1: ['educational_standards'],
            8: ['resources'],
            }

    def get(self):
        user = self.personalize_page_and_get_wiki_user()
        if not user:
            return

        unit = None
        try:
            unit = int(self.request.GET.get('unit', ''))
        except ValueError:
            pass
        if not unit:
            self.redirect('/')
            return

        field_names = self.resource_field_name.get(unit, None)
        if not field_names:
            self.template_value['content'] = Markup(
                    'Sorry, there are no public resources for unit %d'
                    ) % unit
            self.render('bare.html')
            return

        # if we do "all groups" we probably still want to group by group...
        all_groups = self.request.GET.get('all', False)

        query = WikiPage.all().filter('unit', unit)
        query.filter('is_draft', False)
        if not all_groups:
            query.filter('group_id', user.group_id)

        def author_and_fields(pages):
            for p in pages:
                yield (p.author,
                        [ getattr(p, field) for field in field_names ])


        self.template_value['resources'] = author_and_fields(query.run())
        self.template_value['group_id'] = 'All Groups' if all_groups else user.group_id
        self.template_value['unit'] = unit
        self.render('wf_class_wiki.html')


class WarmupHandler(WikiBaseHandler):
    def get(self):
        # warm up the caches for jinja templates
        self.template_value['fields'] = {}
        self.template_value['navbar'] = {}
        self.template_value['unit'] = {}
        self.template_value['student_link'] = str
        self.template_value['action_url'] = list
        self.template_value['create_xsrf_token'] = list
        self.template_value['comments'] = []
        self.render('wf_page.html')
        self.render('wf_profile.html')


from ranking import IntegerRankingField
class RankTestHandler(BaseHandler):
    class Form(wtf.Form):
        rank = IntegerRankingField(label='My Label',
                choices=['Batman', 'Robin', 'An Actual Bat'])
        rank2 = IntegerRankingField(label='My Label 2',
                choices=['Eating', 'Sleeping', 'Dancing', 'Reading'])

    def get(self):
        self.template_value['form'] = self.Form()
        self.render('ranktest.html')

    def post(self):
        form = self.Form(self.request.POST)
        form.validate()
        self.template_value['got_data'] = form.data
        self.template_value['form'] = form
        self.render('ranktest.html')




module = None

def register_module():
    global module

    from report_handlers import EvidenceHandler, BulkIssuanceHandler, SingleIssueHandler, DammitHandler, ExpertEvidenceHandler
    handlers = [
            ('/ranktest', RankTestHandler),
            ('/wiki', WikiPageHandler),
            ('/classwiki', ClassWikiHandler),
            ('/wikicomment', WikiCommentHandler),
            ('/wikiprofile', WikiProfileHandler),
            ('/notification', NotificationHandler),
            ('/all_notifications', NotificationListHandler),
            ('/participants', WikiProfileListHandler),
            ('/_ah/warmup', WarmupHandler),
            ('/updates', WikiUpdateListHandler),
            ('/comment_stream', WikiCommentStreamHandler),
            ('/grump', HarrumphHandler),
            ('/exam_reset', ExamResetHandler),
            ('/badges/evidence', EvidenceHandler),
            ('/badges/expert_evidence', ExpertEvidenceHandler),
            ('/badges/bulk_issue', BulkIssuanceHandler),
            ('/badges/single_issue', SingleIssueHandler),
            ('/badges/dammit', DammitHandler),
            ('/student/comments', CommentListHandler),
            ('/student/endorsements', EndorsementListHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Wikifolios", "Wikifolio pages",
            [], handlers)

    return module

