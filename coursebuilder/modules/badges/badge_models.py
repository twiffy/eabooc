from google.appengine.ext import db
from models.models import BaseEntity, Student
from webapp2 import cached_property
from jinja2 import Markup

class Issuer(BaseEntity):
    # Fields from the OBI specification
    name = db.StringProperty(indexed=False)
    url = db.LinkProperty(indexed=False)
    email = db.EmailProperty(indexed=False)

    def __str__(self):
        return '%s: %s' % (
                type(self).__name__,
                self.key().name(),
                )


class Badge(BaseEntity):
    # Fields from the OBI specification
    name = db.StringProperty(indexed=False)
    description = db.StringProperty(indexed=False)
    image = db.LinkProperty(indexed=False)
    criteria = db.TextProperty() # Served from a separate link...
    issuer = db.ReferenceProperty(Issuer)
    tags = db.StringListProperty(indexed=False)
    # Don't know how to do this well yet...
    # alignment = ...

    def __str__(self):
        return '%s: %s' % (
                type(self).__name__,
                self.key().name(),
                )

class BadgeAssertion(BaseEntity):
    # Fields from the OBI specification
    issuedOn = db.DateProperty()
    expires = db.DateProperty(indexed=False)
    badge = db.ReferenceProperty(Badge, collection_name='assertions')
    recipient = db.ReferenceProperty(Student, collection_name='badges')

    # evidence: how to store this?

    @cached_property
    def recipient_email(self):
        return BaseEntity.recipient.get_value_for_datastore(self).name()

    @cached_property
    def uid(self):
        return 'booc.assertion.' + self.key().id_or_name()

    # @cached_property
    # def recipient_dict(self):
    #     return {
    #             'type': 'email',
    #             'hashed': True,
    #             'not done': True,
    #             }

    def __str__(self):
        return '%s: %s' % (
                type(self).__name__,
                self.key().id_or_name(),
                )
    
