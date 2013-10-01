from models import models
from google.appengine.ext import db
from google.appengine.ext import deferred
from webapp2 import cached_property
import urllib
import logging

class WikiPage(db.Expando):
    unit = db.IntegerProperty()
    edited_timestamp = db.DateTimeProperty(auto_now=True)
    is_draft = db.BooleanProperty(default=False)
    # keep update time?  keep history????

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
        key = cls._key_for_page_cache(page)

        results = models.MemcacheManager.get(key)
        if not results:
            query = page.comments
            results = query.run(limit=1000)
            deferred.defer(cls.cache_comments_on_page, page.key())

        return results

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
        self._invalidate_cache()
        super(WikiComment, self).put()

    def delete(self):
        self._invalidate_cache()
        super(WikiComment, self).delete()

    def is_reply(self):
        return WikiComment.parent_comment.get_value_for_datastore(self) != None

class Annotation(models.BaseEntity):
    """Endorsements, flags-as-abuse, and exemplaries."""
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
    reason = db.StringProperty()

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

class Notification(models.BaseEntity):
    recipient = db.ReferenceProperty(models.Student, collection_name="notification_set")
    url = db.StringProperty(indexed=False)
    text = db.StringProperty(indexed=False)
    seen = db.BooleanProperty(default=False)

    @property
    def link(self):
        return '/notification?id=%d' % self.key().id()


