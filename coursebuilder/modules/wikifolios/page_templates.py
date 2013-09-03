#!/usr/bin/env python
import wtforms as wtf
import bleach
from jinja2 import Markup
from google.appengine.ext import db
from wiki_bleach import BleachedTextAreaField

templates = {}
forms = {}
class ProfilePageForm(wtf.Form):
    text = BleachedTextAreaField('Introduction')
    curricular_aim = BleachedTextAreaField('Curricular Aim')

forms['profile'] = ProfilePageForm
templates['profile'] = 'wf_profile.html'

class UnitOnePageForm(wtf.Form):
    role = BleachedTextAreaField('Curricular Aim')
    setting = BleachedTextAreaField('Curricular Aim')
    curricular_aim = BleachedTextAreaField('Curricular Aim')
    instructional_context = BleachedTextAreaField('Curricular Aim')

forms[1] = UnitOnePageForm
templates[1] = 'wf_temp_u1.html'

def viewable_model(model):
    # TODO maybe default values?
    d = db.to_dict(model)
    return { k: Markup(v) for k,v in d.items() }


