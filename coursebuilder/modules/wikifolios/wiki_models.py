from models import models
from google.appengine.ext import db

class WikiPage(models.BaseEntity):
    text = db.TextProperty()
    unit = db.IntegerProperty()
    # keep update time?  keep history????

    @property
    def author(self):
        return self.parent()

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
    def get_page(cls, user, unit=None):
        key = cls.get_key(user, unit)
        if not key:
            return None
        return cls.get(key)

class WikiComment(models.BaseEntity):
    author = db.ReferenceProperty(models.Student, collection_name="wiki_comments")
    topic = db.ReferenceProperty(WikiPage, collection_name="comments")
    added_time = db.DateTimeProperty(auto_now_add=True)
    text = db.TextProperty()
    # May need to store some stuff about the author in this model,
    # so that it isn't fetched all the time?
    # Or maybe cache it???  Can ReferenceProperty be smart enough
    # to consult the cache?

