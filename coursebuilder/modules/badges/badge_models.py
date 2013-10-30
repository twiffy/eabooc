from google.appengine.ext import db
from models.models import BaseEntity, Student
from webapp2 import cached_property
from jinja2 import Markup
import datetime
import logging

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
    image = db.StringProperty(indexed=False)
    criteria = db.TextProperty() # Served from a separate link...
    evidence_page_criteria = db.TextProperty()
    issuer = db.ReferenceProperty(Issuer)
    tags = db.StringListProperty(indexed=False)
    # Don't know how to do this well yet...
    # alignment = ...

    def __str__(self):
        return '%s: %s' % (
                type(self).__name__,
                self.key().name(),
                )

    @classmethod
    def issue(cls, badge_or_key, recipient, expires=None, put=True):
        existing = BadgeAssertion.all().filter('recipient', recipient).filter('badge', badge_or_key).filter('revoked', False).fetch(30)
        if len(existing) > 0:
            assertion = existing.pop()
            if len(existing) > 0:
                logging.warning('There is more than one assertion tying %s to %s, revoking extras.', recipient, badge_or_key)
                to_put = []
                for e in existing:
                    e.revoked = True
                    to_put.append(e)
                db.put(to_put)
        else:
            assertion = BadgeAssertion(
                    badge=badge_or_key,
                    recipient=recipient)

        assertion.issuedOn = datetime.date.today()
        assertion.expires = expires
        assertion.badge = badge_or_key
        assertion.recipient = recipient
        assertion.revoked = False

        if put:
            assertion.put()
        return assertion

    @classmethod
    def ensure_not_issued(cls, badge_or_key, recipient):
        existing = BadgeAssertion.all().filter('recipient', recipient).filter('badge', badge_or_key).filter('revoked', False).run()
        to_put = []
        for e in existing:
            e.revoked = True
            to_put.append(e)

        db.put(to_put)

    @classmethod
    def is_issued_to(cls, badge_or_key, recipient):
        "If the recipient has got this badge, returns the assertion, otherwise None."
        q = BadgeAssertion.all()
        q.filter('badge', badge_or_key)
        q.filter('recipient', recipient)
        q.filter('revoked', False)
        return q.get()


class BadgeAssertion(BaseEntity):
    # Fields from the OBI specification
    issuedOn = db.DateProperty()
    expires = db.DateProperty(indexed=False)
    badge = db.ReferenceProperty(Badge, collection_name='assertions')
    recipient = db.ReferenceProperty(Student, collection_name='badge_assertions')
    revoked = db.BooleanProperty(default=False)

    evidence = db.StringProperty() # URL of evidence

    @cached_property
    def badge_name(self):
        return BadgeAssertion.badge.get_value_for_datastore(self).name()

    @cached_property
    def recipient_email(self):
        return BadgeAssertion.recipient.get_value_for_datastore(self).name()

    @cached_property
    def uid(self):
        return 'booc.assertion.' + str(self.key().id_or_name())

    def __str__(self):
        return '%s: %s' % (
                type(self).__name__,
                self.key().id_or_name(),
                )
