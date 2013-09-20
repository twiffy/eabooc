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
    role = BleachedTextAreaField()
    setting = BleachedTextAreaField()
    curricular_aim = BleachedTextAreaField()
    instructional_context = BleachedTextAreaField()
    educational_standards = BleachedTextAreaField()
    what_to_assess = BleachedTextAreaField()
    big_ideas = BleachedTextAreaField()
    self_check = BleachedTextAreaField()
    pondertime = BleachedTextAreaField()
    reflection = BleachedTextAreaField()

forms[1] = UnitOnePageForm
templates[1] = 'wf_temp_u1.html'


class UnitTwoPageForm(wtf.Form):
    context = BleachedTextAreaField()
    ranking = BleachedTextAreaField()
    create_items = BleachedTextAreaField()
    commandments = BleachedTextAreaField()
    big_ideas = BleachedTextAreaField()
    self_check = BleachedTextAreaField()
    pondertime = BleachedTextAreaField()
    reflection = BleachedTextAreaField()

forms[2] = UnitTwoPageForm
templates[2] = 'wf_temp_u2.html'


class UnitThreePageForm(wtf.Form):
    context = BleachedTextAreaField()
    ranking = BleachedTextAreaField()
    create_short_answer = BleachedTextAreaField()
    short_answer_guidelines = BleachedTextAreaField()
    create_essay = BleachedTextAreaField()
    essay_guidelines = BleachedTextAreaField()
    essay_key = BleachedTextAreaField()
    essay_scoring_guidelines = BleachedTextAreaField()
    big_ideas = BleachedTextAreaField()
    flawed_item = BleachedTextAreaField()
    item_format_pros_cons = BleachedTextAreaField()
    self_check = BleachedTextAreaField()
    pondertime = BleachedTextAreaField()
    reflection = BleachedTextAreaField()

forms[3] = UnitThreePageForm
templates[3] = 'wf_temp_u3.html'

def viewable_model(model):
    # TODO maybe default values?
    d = db.to_dict(model)
    return { k: Markup(v) for k,v in d.items() }


