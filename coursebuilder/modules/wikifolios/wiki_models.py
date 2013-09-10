from models import models
from google.appengine.ext import db
from webapp2 import cached_property
import urllib
import logging

class WikiPage(db.Expando):
    unit = db.IntegerProperty()
    edited_timestamp = db.DateTimeProperty(auto_now=True)
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
        models.MemcacheManager.delete(self._recents_memcached_key())
        return super(WikiPage, self).put()

    @classmethod
    def _recents_memcached_key(cls):
        return 'recent-entities:%s' % (cls.__name__)

    @classmethod
    def most_recent(cls, count):
        key = cls._recents_memcached_key()
        asked_for_key = key + ":asked-for-how-many"
        recent = models.MemcacheManager.get(key)
        asked_for = models.MemcacheManager.get(asked_for_key)
        if not recent or asked_for != count:
            logging.info("RECALCULATING recent wikifolio updates")
            recent = list(WikiPage.all().order('-edited_timestamp').fetch(limit=count))
            if recent:
                for r in recent:
                    # cache authors
                    x = r.author
                models.MemcacheManager.set(key, recent)
                models.MemcacheManager.set(asked_for_key, count)
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
    sort_key = db.StringProperty(indexed=True)

    #def __init__(self, *args, **kwargs):
        #super(WikiComment, self).__init__(*args, **kwargs)
        ## the default thred of a comment is the comment itself
        #if not self.thread_id and self.is_saved():
            #self.thread_id = self.key().id()

    def _set_sort_key(self, put=False):
        if not self.sort_key:
            time_fmt = '%Y-%j-%H-%M-%S-%f'
            self_key = self.added_time.strftime(time_fmt)
            if not self.is_reply():
                self.sort_key = self_key
            else:
                self.parent_comment._set_sort_key(put=True)
                self.sort_key = self.parent_comment.sort_key
            if put:
                self.put()
        return self.sort_key

    def put(self):
        self._set_sort_key()
        super(WikiComment, self).put()

    def is_reply(self):
        return self.parent_comment != None

class Annotation(models.BaseEntity):
    """Endorsements, flags-as-abuse, and exemplaries."""
    why = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)
    who = db.ReferenceProperty(models.Student, collection_name="own_annotations")
    what = db.ReferenceProperty(collection_name="annotations")

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
        ann.optional_parts_done = optional_done
        ann.put()

    @classmethod
    def endorsements(cls, what=None, who=None):
        q = Annotation.all()
        q.filter("why =", "endorse")
        if what:
            q.filter("what =", what)
        if who:
            q.filter("who =", who)
        return q

    @classmethod
    def exemplary(cls, what, who, reason):
        ann = Annotation()
        ann.why = 'exemplary'
        ann.who = who
        ann.what = what
        ann.reason = reason
        ann.put()

    @classmethod
    def exemplaries(cls, what=None, who=None):
        q = Annotation.all()
        q.filter("why =", "exemplary")
        if what:
            q.filter("what =", what)
        if who:
            q.filter("who =", who)
        return q
