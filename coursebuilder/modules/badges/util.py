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

class BadgeJSONEncoder(json.JSONEncoder):
    def __init__(self, baseurl):
        super(BadgeJSONEncoder, self).__init__()
        self.baseurl = baseurl

    def default(self, obj):
        url = None
        ret = None
        if isinstance(obj, db.Key):
            kind = obj.kind()
            # TODO use dict
            if kind == 'Issuer':
                url = ISSUER_URL
            elif kind == 'BadgeAssertion':
                url = ASSERTION_URL
            elif kind == 'Badge':
                url = BADGE_URL
            elif kind == 'Student':
                ret = recipient_section(obj.name())

            if url:
                ret = '?'.join((
                    self.baseurl + url,
                    urllib.urlencode({
                        'action': 'json',
                        'name': obj.id_or_name()})))
        elif hasattr(obj, 'strftime'):
            ret = obj.strftime('%Y-%m-%d')

        if ret:
            return ret
        return super(BadgeJSONEncoder, self).default(obj)

