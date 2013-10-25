#!/usr/bin/env python
import wtforms as wtf
import bleach
from jinja2 import Markup
from google.appengine.ext import db
from wiki_bleach import BleachedTextAreaField
from ranking import IntegerRankingField

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

class UnitFourPageForm(wtf.Form):
    context = BleachedTextAreaField()
    advantages_disadvantages = BleachedTextAreaField()
    describe = BleachedTextAreaField()
    create_rubric = BleachedTextAreaField()
    evaluate = BleachedTextAreaField()
    big_ideas = BleachedTextAreaField()
    sources_of_error = BleachedTextAreaField()
    impact_on_teaching_learning = BleachedTextAreaField()
    self_check = BleachedTextAreaField()
    pondertime = BleachedTextAreaField()
    reflection = BleachedTextAreaField()

forms[4] = UnitFourPageForm
templates[4] = 'wf_temp_u4.html'

class UnitFivePageForm(wtf.Form):
    context = BleachedTextAreaField()
    types_of_reliability = BleachedTextAreaField()
    standard_error = BleachedTextAreaField()
    absence_of_bias = BleachedTextAreaField()
    big_ideas = BleachedTextAreaField()
    external_resource = BleachedTextAreaField()
    self_check = BleachedTextAreaField()
    pondertime = BleachedTextAreaField()
    reflection = BleachedTextAreaField()

forms[5] = UnitFivePageForm
templates[5] = 'wf_temp_u5.html'

class UnitSixPageForm(wtf.Form):
    context = BleachedTextAreaField()
    types_of_validity = BleachedTextAreaField()
    validity_evidence = BleachedTextAreaField()
    face_and_consequential = BleachedTextAreaField()
    apply_types = BleachedTextAreaField()
    big_ideas = BleachedTextAreaField()
    consequential_validity = BleachedTextAreaField()
    validity_vs_reliability = BleachedTextAreaField()
    self_check = BleachedTextAreaField()
    pondertime = BleachedTextAreaField()
    reflection = BleachedTextAreaField()

forms[6] = UnitSixPageForm
templates[6] = 'wf_temp_u6.html'

class UnitSevenPageForm(wtf.Form):
    context = BleachedTextAreaField()
    define_formative = BleachedTextAreaField()
    learning_progression = BleachedTextAreaField()
    obstacles = BleachedTextAreaField()
    big_ideas = BleachedTextAreaField()
    implementing = BleachedTextAreaField()
    self_check = BleachedTextAreaField()
    pondertime = BleachedTextAreaField()
    reflection = BleachedTextAreaField()

forms[7] = UnitSevenPageForm
templates[7] = 'wf_temp_u7.html'

class UnitEightPageForm(wtf.Form):
    resources = BleachedTextAreaField()
    batman = IntegerRankingField(choices=['Batman', 'Robin', 'An Actual Bat'],
            validators=[wtf.validators.Optional()])
    batman_justification = BleachedTextAreaField()

forms[8] = UnitEightPageForm
templates[8] = 'wf_temp_u8.html'

def viewable_model(model):
    import logging
    logging.warning('viewable_model called')
    unit = model.unit
    if not unit:
        unit = 'profile'
    form = forms[unit](None, model)
    return { f.id: Markup(f.read_only_view()) for f in form }


