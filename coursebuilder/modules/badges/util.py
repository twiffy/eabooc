#!/usr/bin/env python

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
    m = hashlib.new(algorithm)
    m.update(email)
    m.update(salt)
    return [algorithm,
        m.hexdigest()]

def recipient_section(email):
        hashed = compute_hash(email, salt, algorithm)
        return {
                'identity': '$'.join(hashed),
                'type': 'email',
                'hashed': True,
                'salt': salt,
                }

def url_for_key(obj, action='json'):
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
