#!/usr/bin/env python
"""
Helpers for rendering the badge information to JSON.

This is a clunky way to do it, it could really use a
refactor.
"""
# generate badges for use with Mozilla Open Badge system
# usage: badger.py < list_of_emails.txt

import hashlib
import json
from google.appengine.ext import db
from modules.badges.badge_models import *
from models.models import Student
import datetime
import urllib
from jinja2 import Markup

salt = '041b543b693eb1463d8d7d1213fb16a2'
algorithm = 'sha256'

# TODO make these shared

ISSUER_URL = '/badges/issuer'
BADGE_URL = '/badges/badge'
ASSERTION_URL = '/badges/assertion'


def compute_hash(email, salt, algorithm=None):
    "Compute a hash of an e-mail, for badge assertions."
    m = hashlib.new(algorithm)
    m.update(email)
    m.update(salt)
    return [algorithm,
        m.hexdigest()]

def recipient_section(email):
        "The dictionary/string structure that represents a badge recipient"
        hashed = compute_hash(email, salt, algorithm)
        return {
                'identity': '$'.join(hashed),
                'type': 'email',
                'hashed': True,
                'salt': salt,
                }

def url_for_key(obj, action='json'):
    "Find the URL for a badge object of various kinds"
    kind = obj.kind()
    # TODO use dict
    url = None
    if kind == 'Issuer':
        url = ISSUER_URL
    elif kind == 'BadgeAssertion':
        url = ASSERTION_URL
    elif kind == 'Badge':
        url = BADGE_URL
    if url:
        return '?'.join((
            url,
            urllib.urlencode({
                'action': action,
                'name': obj.id_or_name()})))

class BadgeJSONEncoder(json.JSONEncoder):
    "This is a dumb way to do it, yuck."
    def __init__(self, baseurl, **kwargs):
        super(BadgeJSONEncoder, self).__init__(**kwargs)
        self.baseurl = baseurl

    def default(self, obj):
        ret = None
        if isinstance(obj, db.Key):
            url = url_for_key(obj)
            if url:
                ret = self.baseurl + url
            if obj.kind() == 'Student':
                student = db.get(obj)
                email = student.badge_email
                ret = recipient_section(email)

        elif hasattr(obj, 'strftime'):
            ret = obj.strftime('%Y-%m-%d')

        if ret:
            return ret
        return super(BadgeJSONEncoder, self).default(obj)
