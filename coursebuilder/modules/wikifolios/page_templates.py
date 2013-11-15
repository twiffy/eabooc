#!/usr/bin/env python
import wtforms as wtf
import bleach
from jinja2 import Markup
from google.appengine.ext import db
from wiki_bleach import BleachedTextAreaField
from ranking import IntegerRankingField, StringRankingField

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
    context = BleachedTextAreaField()
    interpreting = BleachedTextAreaField()
    resources = BleachedTextAreaField()
    intended_uses = BleachedTextAreaField()
    actual_uses = BleachedTextAreaField()
    ranking = IntegerRankingField(
            choices=['Percentiles', 'Grade Equivalent Scores', 'Scale Scores'],
            validators=[wtf.validators.Optional()])
    ranking_justification = BleachedTextAreaField()
    big_ideas = BleachedTextAreaField()

    explaining_scores = BleachedTextAreaField()
    race_to_top = BleachedTextAreaField()
    self_check = BleachedTextAreaField()
    pondertime = BleachedTextAreaField()
    reflection = BleachedTextAreaField()

forms[8] = UnitEightPageForm
templates[8] = 'wf_temp_u8.html'

class UnitNinePageForm(wtf.Form):
    context = BleachedTextAreaField()
    guidelines = BleachedTextAreaField()
    selected_scenario = BleachedTextAreaField()
    constructed_scenario = BleachedTextAreaField()

    rank_good_practices = IntegerRankingField(
            choices=['Varied format preparation', 'Generalized test taking preparation'],
            validators=[wtf.validators.Optional()])
    justify_good_practices = BleachedTextAreaField()

    rank_bad_practices = IntegerRankingField(
            choices=['Previous-form preparation',
                'Current-form preparation',
                'Same format preparation',
                ],
            validators=[wtf.validators.Optional()])
    justify_bad_practices = BleachedTextAreaField()

    big_ideas = BleachedTextAreaField()
    perf_port_scenario = BleachedTextAreaField()

    self_check = BleachedTextAreaField()
    pondertime = BleachedTextAreaField()
    reflection = BleachedTextAreaField()

forms[9] = UnitNinePageForm
templates[9] = 'wf_temp_u9.html'

class Unit10PageForm(wtf.Form):
    context = BleachedTextAreaField()

    rank_evaluating_instruction = IntegerRankingField(
            validators=[wtf.validators.Optional()],
            choices=['Evidence from classroom assessments.',
                'Evidence from accountability tests.'],
            labels=[Markup('''This is the evidence
                    you can gather from classroom assessments, ideally when given
                    before and after instruction. These assessments
                    <i>should</i> be aligned
                    to the curricular aim of the instruction. This is
                    explained more on pages 378-383.'''),
                Markup('''This is the
                    evidence that comes from externally developed tests. &nbsp;As
                    explained on pages 383-398, these may or may not be sensitive
                    to the instruction provided to students before a particular
                    test.''')],
            )
    justify_evaluating_instruction = BleachedTextAreaField()

    rank_classroom_evidence = IntegerRankingField(
            validators=[wtf.validators.Optional()],
            choices=['Pretests Versus Posttests.',
                'Split-and-Switch Design.'],
            labels=[
                Markup('''This is where you give the same assessment before and
                    after instruction. &nbsp;As explained in the book
                    and <span class="c9 c2"><a class="c4" target="_blank"
                    href=
                    "http://www.bumc.bu.edu/fd/files/PDF/Pre-andPost-Tests.pdf">here</a></span>, this
                    is easy but problematic.'''),
                Markup('''
                    This is sometimes called "split-half" and uses a
                    technique called counter-balancing. &nbsp;As explained in the
                    book and <span class="c9 c2"><a class="c4" target="_blank"
                    href=
                    "http://www.k12.hi.us/~bwoerner/ipcs/ip4studperf.html">here
                    (scroll down)</a></span>, it is more
                    effective but can be challenging to do.'''),
                ]
            )
    justify_classroom_evidence = BleachedTextAreaField()

    rank_sensitivity = IntegerRankingField(
            validators=[wtf.validators.Optional()],
            choices=['Alignment Leniency:',
                'Excessive Easiness:',
                'Excessive Difficulty:',
                'Item Flaws:',
                'Socioeconomic Status Links:',
                'Academic Aptitude Links:'],
            labels=[
                Markup('''When the test item is
                    not aligned to (does not measure) the curricular aim thought to
                    be measured. This means the item is measuring something other
                    than the curricular aim.'''),
                Markup('''The test item is so easy
                    that students who were not even taught will answer the item
                    correctly; so the test item does not measure student
                    achievement on the curricular aim.'''),
                Markup('''The test items are so
                    difficult that even students who mastered the curricular aim
                    will not answer it correctly; so the item does not distinguish
                    between well-taught and poorly taught students.'''),
                Markup('''Errors in the test item
                    itself cause students to answer the item incorrectly; so the
                    item does not distinguish between well-taught and poorly taught
                    students.'''),
                Markup('''When a test item unfairly
                    advantages students from higher SES statuses and so the item
                    measures the knowledge students bring to school rather than how
                    they are taught within the classroom.'''),
                Markup('''When
                    a test item unfairly advantages students coming to the
                    classroom with already higher quantitative, verbal, or spatial
                    aptitudes and so the item measures the knowledge students bring
                    to school rather than how they are taught within the
                    classroom.'''),
                ]
            )
    justify_sensitivity = BleachedTextAreaField()

    rank_evaluating_teaching = StringRankingField(
            validators=[wtf.validators.Optional()],
            choices=[
                ('gates', Markup('''<span class="c2">Gates
                    Foundation</span><span class="c2"><a class="c4" target="_blank" href=
                    "http://www.gatesfoundation.org/media-center/press-releases/2013/01/measures-of-effective-teaching-project-releases-final-research-report">&nbsp;</a></span><span class="c9 c2"><a class="c4"
                    target="_blank" href=
                    "http://www.gatesfoundation.org/media-center/press-releases/2013/01/measures-of-effective-teaching-project-releases-final-research-report">Measures
                    of Effective Teaching Report</a></span><span class=
                    "c2">&nbsp;and</span><span class="c2"><a class="c4" target="_blank" href=
                    "http://www.metproject.org/index.php">&nbsp;</a></span><span class="c9 c2"><a class="c4"
                    target="_blank" href="http://www.metproject.org/index.php">Website &amp;
                    Videos</a></span><span class="c2">. &nbsp;The executive summary
                    of the report is a very helpful overview of this influential
                    report.</span>''')),
                ('guarino', Markup('''<span class="c9 c2"><a class="c4" target="_blank" href=
                    "/assets/content/guarino-policy-brief.pdf">Policy Brief: Highlights of
                    Conference on Using Student Test Scores to Measure Teacher
                    Performance</a></span><span class="c2">&nbsp;(pdf, Cassandra
                    Guarino).</span>''')),
                ('darling-hammond', Markup('''<span class=
                    "c2">Video from the Aspen Institute on the</span><span class=
                    "c9 c2"><a class="c4" target="_blank" href=
                    "https://www.youtube.com/watch?v=7JUrYwcd68E">&nbsp;Role of
                    Teacher Evaluation in Reforming Public</a></span><span class=
                    "c9 c2">&nbsp;</span><span class="c2">Schools</span>''')),
                ('tapsystem', Markup('''<span class="c9 c2"><a class="c4" target="_blank" href=
                    "http://www.tapsystem.org/policyresearch/policyresearch.taf?page=valueadded">Understanding
                    Value-Added Analysis of Student
                    Achievement.</a></span><span class="c2">&nbsp; This is a bit
                    outdated but there are some links to excellent resources at the
                    bottom of the page.</span>''')),
                ('rand', Markup('''<span class="c9 c2"><a class="c4" target="_blank" href=
                    "http://www.rand.org/topics/value-added-modeling-in-education.html">Value
                    Added Modeling in Education</a></span><span class=
                    "c2">&nbsp;(RAND Corporation). &nbsp;Probably one of the most
                    comprehensive websites out there. Very current and easy to
                    navigate.</span>''')),
                ])
    justify_evaluating_teaching = BleachedTextAreaField()

    big_ideas = BleachedTextAreaField()
    self_check = BleachedTextAreaField()
    pondertime = BleachedTextAreaField()
    reflection = BleachedTextAreaField()

forms[10] = Unit10PageForm
templates[10] = 'wf_temp_u10.html'

class Unit11PageForm(wtf.Form):
    context = BleachedTextAreaField()
    evaluation_options = BleachedTextAreaField()
    goal_scenario = BleachedTextAreaField()
    rank_evaluation_options = IntegerRankingField(
            validators=[wtf.validators.Optional()],
            choices=[
                'Absolute Grading',
                'Relative Grading',
                'Aptitude-Based Grading',
                'Standards-Based Grading',
                'Goal-Attainment Grading'])
    justify_evaluation_options = BleachedTextAreaField()
    big_ideas = BleachedTextAreaField()

    rank_grading_specifics = StringRankingField(
            validators=[wtf.validators.Optional()],
            choices=[
                ('different-approaches', '''Different approaches to
                    grading (ex. achievement-level, standards-based
                    report cards, descriptive feedback)'''),
                ('evaluative', 'Evaluative options (listed above)'),
                ('effort', '''Effort (Popham says you should never
                    grade for 'effort' but many people disagree)'''),
                ('intangible', '''Intangible Factors (also called Evaluative
                    Factors, this includes things like study
                    skills and social skills)'''),
                ('record-keeping', 'Record keeping (i.e., handwritten versus electronic)'),
                ('conferences', 'Grading conferences (who gets to be involved?)'),
                ('imprecision', 'Imprecision (mistakes and bias)'),
                ])
    justify_grading_specifics = BleachedTextAreaField()
    self_check = BleachedTextAreaField()
    pondertime = BleachedTextAreaField()
    reflection = BleachedTextAreaField()

forms[11] = Unit11PageForm
templates[11] = 'wf_temp_u11.html'


def viewable_model(model):
    unit = model.unit
    if not unit:
        unit = 'profile'
    form = forms[unit](None, model)
    return { f.id: Markup(f.read_only_view()) for f in form }


