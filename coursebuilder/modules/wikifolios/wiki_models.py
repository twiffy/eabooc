from models import models
from google.appengine.ext import db
import urllib
import logging

class WikiPage(models.BaseEntity):
    text = db.TextProperty()
    title = db.StringProperty()
    unit = db.IntegerProperty()
    # keep update time?  keep history????

    @property
    def author(self):
        return self.parent()

    @property
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


class WikiComment(models.BaseEntity):
    author = db.ReferenceProperty(models.Student, collection_name="wiki_comments")
    topic = db.ReferenceProperty(WikiPage, collection_name="comments")
    added_time = db.DateTimeProperty(auto_now_add=True)
    text = db.TextProperty()
    # May need to store some stuff about the author in this model,
    # so that it isn't fetched all the time?
    # Or maybe cache it???  Can ReferenceProperty be smart enough
    # to consult the cache?

class Annotation(models.BaseEntity):
    """Endorsements, flags-as-abuse, and exemplaries."""
    why = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)
    who = db.ReferenceProperty(models.Student, collection_name="own_annotations")
    what = db.ReferenceProperty(collection_name="annotations")

    # for endorsements:
    optional_parts_done = db.BooleanProperty()

    # for exemplaries:
    comment = db.ReferenceProperty(WikiComment, collection_name="exemplary_marks")

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
    def exemplary(cls, what, who, comment):
        ann = Annotation()
        ann.why = 'exemplary'
        ann.who = who
        ann.what = what
        ann.comment = comment
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
