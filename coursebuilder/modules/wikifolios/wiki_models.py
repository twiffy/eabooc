"Database models representing Wikifolio-related things"
from datetime import datetime
from models import models
from google.appengine.ext import db
from google.appengine.ext import deferred
from webapp2 import cached_property
import urllib
import logging

class WikiPage(db.Expando):
    """
    A page in someone's wikifolio, either a unit or their profile page.

    WikiPages are datastore ancestors of the students who write them,
    and the key name is either "unit:%d" % unit_id, or 'profile'.  This
    prevents duplicates, but is also awkward in some ways.  For example,
    you can't make a link to this page without having the author's datastore
    object, for their wiki_id number.  Maybe someone should add a permalink
    method, like the one for comments... but it can't be based on the key ID,
    because the student's e-mail is encoded in it.  Hmmm.
    """
    unit = db.IntegerProperty()
    edited_timestamp = db.DateTimeProperty(auto_now=True)
    is_draft = db.BooleanProperty(default=False)
    group_id = db.StringProperty(default='')

    @cached_property
    def author(self):
        author = models.Student.get_enrolled_student_by_email(self.author_email)
        if not author:
            author = self.parent()
        return author

    @cached_property
    def author_key(self):
        # get_value_for_datastore(etc) doesn't work on the above author property...
        return self.key().parent()

    @cached_property
    def author_email(self):
        return self.key().parent().name()

    @cached_property
    def link(self):
        student = self.author.wiki_id
        params = {
            'student': student,
            'action': 'view',
            }
        if self.unit:
            params['unit'] = self.unit
            return 'wiki?' + urllib.urlencode(params)
        else:
            return 'wikiprofile?' + urllib.urlencode(params)


    @classmethod
    def query_by_student(cls, student):
        # Encapsulate that the student->page relationship
        # is by key path, not some other way.
        return cls.all().ancestor(student.key())

    @classmethod
    def get_key(cls, user, unit=None):
        "Return the key to the wikipage for the given user, and the given unit (or None for profile page)"
        if not user:
            return None
        if unit:
            return db.Key.from_path(
                    'Student', user.key().name(),
                    'WikiPage', 'unit:%d' % unit)
        else:
            return db.Key.from_path(
                    'Student', user.key().name(),
                    'WikiPage', 'profile')

    @classmethod
    def get_page(cls, user, unit=None, create=False):
        "Get a WikiPage object for a given student/unit.  Optionally create it if it doesn't exist"
        key = cls.get_key(user, unit)
        if not key:
            return None
        page = cls.get(key)
        if create and not page:
            return cls(key=key)
        return page

    def is_endorsed(self):
        return self.annotations.filter('why', 'endorse').count(limit=1) > 0

    def is_exemplaried(self):
        return self.annotations.filter('why', 'exemplary').count(limit=1) > 0

    def delete(self):
        models.MemcacheManager.delete(self._recents_memcached_key())
        return super(WikiPage, self).delete()

    def put(self):
        # Put, and update the memcache list of most recent edits.
        key = self._recents_memcached_key()
        models.MemcacheManager.delete(key)
        deferred.defer(WikiPage.most_recent)
        return super(WikiPage, self).put()

    @classmethod
    def _recents_memcached_key(cls):
        return 'recent-entities:%s' % (cls.__name__)

    @classmethod
    def most_recent(cls, count=50):
        key = cls._recents_memcached_key()
        asked_for_key = key + ":asked-for-how-many"
        recent = models.MemcacheManager.get(key)
        asked_for = models.MemcacheManager.get(asked_for_key)
        if not recent or asked_for != count:
            logging.info("RECALCULATING recent wikifolio updates")
            recent = list(WikiPage.all().order('-edited_timestamp').filter('is_draft', False).fetch(limit=count))
            if recent:
                for r in recent:
                    # cache authors
                    x = r.author
                models.MemcacheManager.set(key, recent, ttl=60*60*12)
                models.MemcacheManager.set(asked_for_key, count, ttl=60*60*12)
        return recent


class WikiComment(models.BaseEntity):
    """
    A comment on a wikifolio.

    We cheat slightly when sorting the comments - we don't actually traverse the
    tree structure when sorting.  We save the parent comment's timestamp in this
    comment, and then sort using that when viewing the page.
    """
    author = db.ReferenceProperty(models.Student, collection_name="wiki_comments")
    topic = db.ReferenceProperty(WikiPage, collection_name="comments")
    added_time = db.DateTimeProperty(auto_now_add=True)
    text = db.TextProperty()

    editor = db.ReferenceProperty(models.Student, collection_name="wiki_comments_edited")
    edited_time = db.DateTimeProperty(auto_now=True)
    is_edited = db.BooleanProperty()
    is_deleted = db.BooleanProperty()

    parent_comment = db.SelfReferenceProperty(collection_name="replies")
    parent_added_time = db.DateTimeProperty()

    is_author_question = db.BooleanProperty(default=False)

    #def __init__(self, *args, **kwargs):
        #super(WikiComment, self).__init__(*args, **kwargs)
        ## the default thred of a comment is the comment itself
        #if not self.thread_id and self.is_saved():
            #self.thread_id = self.key().id()

    @cached_property
    def author_email(self):
        return WikiComment.author.get_value_for_datastore(self).name()

    def _cache_author(self):
        try:
            author = models.Student.get_enrolled_student_by_email(self.author_email)
        except:
            pass
        if not author:
            author = self.author
        type(self).author.__set__(self, author)

    @classmethod
    def _key_for_page_cache(cls, page):
        if type(page) is str:
            page = db.Key(page)
        elif type(page) is not db.Key:
            page = page.key()
        return 'comments-by-page:%s' % page

    @classmethod
    def comments_on_page(cls, page):
        return page.comments.run(limit=1000)

        # key = cls._key_for_page_cache(page)

        # results = models.MemcacheManager.get(key)
        # if not results:
        #     query = page.comments
        #     results = query.run(limit=1000)
        #     deferred.defer(cls.cache_comments_on_page, page.key())

        # return results

    @classmethod
    def cache_comments_on_page(cls, page_key):
        results = WikiComment.all().filter('topic', page_key).run(limit=1000)
        key = cls._key_for_page_cache(page_key)
        models.MemcacheManager.set(key, list(results), ttl=60*60*48)

    def _set_sort_key(self):
        if self.is_reply() and not self.parent_added_time:
            self.parent_added_time = self.parent_comment.added_time

    def _invalidate_cache(self):
        key = self._key_for_page_cache(self.topic)
        models.MemcacheManager.delete(key)
        deferred.defer(self.cache_comments_on_page, self.topic.key())

    def put(self):
        self._set_sort_key()
        super(WikiComment, self).put()
        self._invalidate_cache()

    def delete(self):
        super(WikiComment, self).delete()
        self._invalidate_cache()

    def is_reply(self):
        return WikiComment.parent_comment.get_value_for_datastore(self) != None

class Annotation(models.BaseEntity):
    """Endorsements, flags-as-abuse, exemplaries, Dan reviews, incompletes."""
    why = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)
    who = db.ReferenceProperty(models.Student, collection_name="own_annotations")
    what = db.ReferenceProperty(WikiPage, collection_name="annotations")
    unit = db.IntegerProperty()
    whose = db.ReferenceProperty(models.Student, collection_name="annotations_of")

    # for endorsements:
    optional_parts_done = db.BooleanProperty()

    # for exemplaries:
    # for flags:
    reason = db.TextProperty()

    @cached_property
    def whose_email(self):
        key = Annotation.whose.get_value_for_datastore(self)
        if not key:
            # wat.
            logging.info('Doing extra slow query, %s has no .whose',
                    str(self.key()))
            self.whose = self.what.author
            self.put()
            return self.whose.key().name()
        return key.name()

    @classmethod
    def flag(cls, what, who, reason):
        ann = Annotation()
        ann.why = 'flag'
        ann.who = who
        ann.what = what
        ann.reason = reason
        ann.put()

    @classmethod
    def endorse(cls, what, who, optional_done):
        ann = Annotation()
        ann.why = 'endorse'
        ann.who = who
        ann.what = what
        ann.unit = what.unit
        ann.whose = what.author_key
        ann.optional_parts_done = optional_done
        ann.put()

    # TODO: make this interface a little nicer?  Or elminate it...
    @classmethod
    def endorsements(cls, what=None, who=None, unit=None, whose=None):
        q = Annotation.all()
        q.filter("why =", "endorse")
        if what:
            q.filter("what =", what)
        if who:
            q.filter("who =", who)
        if unit:
            q.filter("unit =", unit)
        if whose:
            q.filter("whose = ", whose)
        return q

    @classmethod
    def exemplary(cls, what, who, reason):
        ann = Annotation()
        ann.why = 'exemplary'
        ann.who = who
        ann.what = what
        ann.unit = what.unit
        ann.whose = what.author_key
        ann.reason = reason
        ann.put()

    @classmethod
    def exemplaries(cls, what=None, who=None, unit=None, whose=None):
        q = Annotation.all()
        q.filter("why =", "exemplary")
        if what:
            q.filter("what =", what)
        if who:
            q.filter("who =", who)
        if unit:
            q.filter("unit =", unit)
        if whose:
            q.filter("whose = ", whose)
        return q

    @classmethod
    def incomplete(cls, what, who, reason):
        ann = Annotation()
        ann.why = 'incomplete'
        ann.who = who
        ann.what = what
        ann.unit = what.unit
        ann.whose = what.author_key
        ann.reason = reason
        ann.put()

    @classmethod
    def incompletes(cls, what=None, who=None, unit=None, whose=None):
        q = Annotation.all()
        q.filter("why =", "incomplete")
        if what:
            q.filter("what =", what)
        if who:
            q.filter("who =", who)
        if unit:
            q.filter("unit =", unit)
        if whose:
            q.filter("whose = ", whose)
        return q

    @classmethod
    def review(cls, what, who, text):
        ann = Annotation()
        ann.why = 'review'
        ann.who = who
        ann.what = what
        ann.unit = what.unit
        ann.whose = what.author_key
        ann.reason = text
        ann.put()

    @classmethod
    def reviews(cls, what=None, who=None, unit=None, whose=None):
        q = Annotation.all()
        q.filter('why =', 'review')
        if what:
            q.filter("what =", what)
        if who:
            q.filter("who =", who)
        if unit:
            q.filter("unit =", unit)
        if whose:
            q.filter("whose = ", whose)
        return q


class Notification(models.BaseEntity):
    "Notifications for users, for example links to announcements"
    recipient = db.ReferenceProperty(models.Student, collection_name="notification_set")
    url = db.StringProperty(indexed=False)
    text = db.StringProperty(indexed=False)
    seen = db.BooleanProperty(default=False)
    created = db.DateTimeProperty(auto_now_add=True)
    touched = db.DateTimeProperty(auto_now=True)

    @property
    def link(self):
        return '/notification?id=%d' % self.key().id()

    @staticmethod
    def sort_key_func(note):
        return note.created if note.created else datetime.min

    @classmethod
    def notify_all_students(cls, url, text, defer=True):
        if defer:
            deferred.defer(
                    cls.notify_all_students, url, text, defer=False)
            return

        all_students = models.Student.all().filter('is_participant', True).run(keys_only=True)
        to_put = []
        for student in all_students:
            note = cls(recipient=student, url=url, text=text)
            to_put.append(note)
        db.put(to_put)
