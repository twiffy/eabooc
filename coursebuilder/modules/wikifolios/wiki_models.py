from models.models import BaseEntity
from google.appengine.ext import db

class WikiPage(BaseEntity):
    text = db.TextProperty()
    unit = db.IntegerProperty()

    @classmethod
    def get_key(cls, user, unit=None):
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
        return cls.get(key)

