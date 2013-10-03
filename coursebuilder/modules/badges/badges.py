from models import custom_modules
from google.appengine.ext import deferred
from models.models import Student
from models.roles import Roles
from modules.regconf.regconf import FormSubmission
from controllers.utils import BaseHandler, ReflectiveRequestHandler
from google.appengine.ext import db
from google.appengine.api import users
import logging
import unicodecsv as csv
import wtforms as wtf
from wtforms.ext.appengine.db import model_form
from markupsafe import Markup
from modules.wikifolios.wiki_models import *
import modules.wikifolios.wikifolios as wf
from modules.wikifolios.page_templates import forms, viewable_model
from collections import defaultdict
import urllib
import re
import itertools
from common import prefetch

import util
from badge_models import *

import json

not_specified = object()

class BadgeItemHandler(BaseHandler, ReflectiveRequestHandler):
    # JSON is the only public view from this handler.
    default_action = 'list'
    get_actions = ['view', 'json', 'edit', 'list']
    post_actions = ['save']

    def _action_url(self, action, name=not_specified):
        if name is not_specified:
            name = self.request.GET['name']
        params = {
                'name': name,
                'action': action,
                }
        return '?'.join((
            self.request.path,
            urllib.urlencode(params)))

    def _get_object_or_abort(self, create=False):
        if 'name' not in self.request.GET:
            self.abort(400)

        key_name = self.request.GET['name']
        obj = self.KIND.get_by_key_name(key_name)
        if not obj:
            if not create:
                self.abort(404)
            else: # yes create
                obj = self.KIND(key_name=key_name)
        return obj

    def to_dict(self, obj):
        return db.to_dict(obj)

    def htmlize_fields(self, fields):
        # The JSON version of this is util.BadgeJSONEncoder.
        d = fields
        for k,v in d.iteritems():
            if isinstance(v, db.Key):
                # that is, if the value of the dict is a database key...
                url = util.url_for_key(v, action='view')
                if url:
                    d[k] = Markup('<a href="%(url)s">%(kind)s: %(id)s</a>') % {
                            'url': url,
                            'kind': v.kind(),
                            'id': v.id_or_name(),
                            }
                if v.kind() == 'Student':
                    d[k] = v.name()
        return d

    def get_json(self):
        obj = self._get_object_or_abort()

        self.response.content_type = 'application/json'
        json_encoder = util.BadgeJSONEncoder(self.request.host_url)
        self.response.write(json_encoder.encode(self.to_dict(obj)))

    def get_view(self):
        if not users.is_current_user_admin():
            self.abort(403)
        obj = self._get_object_or_abort()

        self.template_value['action_url'] = self._action_url
        self.template_value['title'] = '%s: %s' % (self.KIND.__name__, obj.key().name())
        fields = self.to_dict(obj)
        self.template_value['fields'] = self.htmlize_fields(fields)
        self.render('badge_item_view.html')

    def get_edit(self):
        if not users.is_current_user_admin():
            self.abort(403)

        obj = self._get_object_or_abort(create=True)
        form = self.FORM(None, obj)
        self.render_edit(form, obj)

    def render_edit(self, form, obj):
        self.template_value['action_url'] = self._action_url
        self.template_value['title'] = 'Edit %s: %s' % (self.KIND.__name__, obj.key().name())
        self.template_value['form'] = form
        self.template_value['xsrf_token'] = self.create_xsrf_token('save')
        self.render('badge_item_edit.html')

    def post_save(self):
        if not users.is_current_user_admin():
            self.abort(403)

        obj = self._get_object_or_abort(create=True)
        form = self.FORM(self.request.POST, obj)
        if not form.validate():
            self.render_edit(form, obj)
            return

        form.populate_obj(obj)
        obj.put()
        self.redirect(self._action_url('view'))

    def get_list(self):
        if not users.is_current_user_admin():
            self.abort(403)

        items = self.KIND.all()
        self.template_value['action_url'] = self._action_url
        self.template_value['title'] = 'List of %s' % self.KIND.__name__
        self.template_value['items'] = items
        actions = list(self.get_actions)
        actions.remove('list')
        self.template_value['actions'] = actions
        self.render('badge_item_list.html')


class BadgeHandler(BadgeItemHandler):
    KIND = Badge
    FORM = model_form(Badge)

    # get_actions = BadgeItemHandler.get_actions + ['issue']

    # def get_issue(self):
    #     # Somehow redirect to the 'create' form of the BadgeAssertion,
    #     # But pre-selecting this badge?
    #     # TODO: is this dumb?
    #     if not users.is_current_user_admin():
    #         self.abort(403)
    #     self.response.write('not there yet..')

    def htmlize_fields(self, fields):
        fields['image'] = Markup('<img src="%s" alt="%s">') % (
                fields['image'], fields['image'])
        return super(BadgeHandler, self).htmlize_fields(fields)


class AssertionHandler(BadgeItemHandler):
    KIND = BadgeAssertion
    FORM = model_form(BadgeAssertion)

    def to_dict(self, obj):
        d = super(AssertionHandler, self).to_dict(obj)
        d['uid'] = obj.uid
        return d


class IssuerHandler(BadgeItemHandler):
    KIND = Issuer
    FORM = model_form(Issuer)


ISSUER_URL = '/badges/issuer'
BADGE_URL = '/badges/badge'
ASSERTION_URL = '/badges/assertion'

module = None

def register_module():
    global module

    handlers = [
            (ISSUER_URL, IssuerHandler),
            (BADGE_URL, BadgeHandler),
            (ASSERTION_URL, AssertionHandler),
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Badges", "Badges",
            [], handlers)

    return module

