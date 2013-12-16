from modules.badges.badge_models import *
from modules.wikifolios.report import *
from modules.wikifolios.wiki_models import *
from google.appengine.ext import db
from models.models import Student
import models.utils

def create_wikifolio_page(student, unit):
    page = WikiPage.get_page(student, unit, create=True)
    page.context = db.Text("This is a test page, lulz!")
    page.unit = unit
    page.put()
    return page


def endorse_all(endorser, author):
    all_pages = WikiPage.query_by_student(author)
    for page in all_pages:
        if not page.unit:
            continue
        Annotation.endorse(page, endorser, True)


def set_score(student, test, score):
    models.utils.set_score(student, test, score)
    student.put()


get_student = Student.get_by_email


part_names = [
        'practices',
        'principles',
        'policies',
        ]

def make_all_basic_badges():
    issuer = Issuer.all().get()
    if not issuer:
        raise NotImplementedError("you gotta make the issuer first")
    for num, part in enumerate(part_names, 1):
        badge = Badge.get_by_key_name(part)
        if not badge:
            badge = Badge(key_name=part)
            badge.name = "Assessment " + part.title()
            badge.description = badge.name
            badge.image = '/assets/img/badges/250px/%02d-%s.png' % (num, part.title())
            badge.criteria = 'Important Stuff'
            badge.evidence_page_criteria = badge.criteria + '(evidence page version)'
            badge.issuer = issuer
            badge.put()
