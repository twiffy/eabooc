from models.models import BaseEntity
from google.appengine.ext import db

class WikiPage(BaseEntity):
    title = db.StringProperty()
    text = db.TextProperty()

