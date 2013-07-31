from models.models import BaseEntity
from google.appengine.ext import db

class WikiPage(BaseEntity):
    text = db.TextProperty()
    unit = db.IntegerProperty()

    @property
    def author(self):
        return self.parent()

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

