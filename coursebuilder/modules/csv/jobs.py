from google.appengine.ext import deferred
from google.appengine.runtime import DeadlineExceededError
from common.querymapper import Mapper
import modules.wikifolios.wiki_models as wm
from google.appengine.api import mail
from google.appengine.ext import db
from models import models
import lxml.etree

class AnnotationUpdateJob(Mapper):
    KIND = wm.Annotation
    count = 0

    def map(self, ann):
        if not ann.unit:
            ann.unit = ann.what.unit
            ann.whose = ann.what.author_key
            self.count += 1
            return ([ann], [])
        return ([], [])

    def finish(self):
        mail.send_mail(sender="booc.class@gmail.com",
                to="thomathom@gmail.com",
                subject="Done updating annotations",
                body="Yeah buddy! Did %d of them!" % self.count)

from modules.wikifolios.wiki_models import *
class WikisPostedUpdateJob(Mapper):
    KIND = models.Student
    count = 0

    def map(self, student):
        student.wikis_posted = []
        pages = WikiPage.query_by_student(student).run(limit=20)
        for p in pages:
            if p.unit:
                student.wikis_posted.append(p.unit)
                self.count += 1
        if student.wikis_posted:
            student.wikis_posted = list(set(student.wikis_posted))
        return ([student], [])

    def finish(self):
        mail.send_mail(sender="booc.class@gmail.com",
                to="thomathom@gmail.com",
                subject="Done updating annotations",
                body="Yeah buddy! Did %d of them!" % self.count)

class WikisDraftJob(Mapper):
    KIND = WikiPage
    count = 0

    def map(self, page):
        page.is_draft = False
        return ([page], [])

    def finish(self):
        mail.send_mail(sender="booc.class@gmail.com",
                to="thomathom@gmail.com",
                subject="Done updating wiki pages",
                body="Yeah buddy! Did %d of them!" % self.count)

class NoteUpdateJob(Mapper):
    KIND = models.Student


    def map(self, student):
        to_put = []
        for n in student.notifications:
            tree = lxml.etree.fromstring(n)
            if tree.tag != 'a':
                logging.warning("%s has a note that is weird: %s", student.key().name(), n)
                return
            url = tree.attrib['href']
            tree.tag = 'span'
            del tree.attrib['href']
            to_put.append(wm.Notification(
                recipient=student,
                url=url,
                text=lxml.etree.tostring(tree)))
        student.notifications = []
        to_put.append(student)
        return (to_put, [])


    def finish(self):
        mail.send_mail(sender="booc.class@gmail.com",
                to="thomathom@gmail.com",
                subject="Done updating notes",
                body="Yeah buddy!")


class CommentSortKeyJob(Mapper):
    KIND = WikiComment

    def map(self, comment):
        comment._set_sort_key()
        return ([comment], [])

    def finish(self):
        mail.send_mail(sender="booc.class@gmail.com",
                to="thomathom@gmail.com",
                subject="Done updating comments",
                body="Yeah buddy!")

class EventEntityIndexerJob(Mapper):
    KIND = models.EventEntity

    def map(self, event):
        return ([event], [])

    def finish(self):
        mail.send_mail(sender="booc.class@gmail.com",
                to="thomathom@gmail.com",
                subject="Done updating event entities",
                body="Yeah buddy!")

class NotificationNoAutoNowJob(Mapper):
    KIND = Notification

    def map(self, note):
        if 'created' not in note._entity:
            note.created = None
        return ([note], [])

    def finish(self):
        mail.send_mail(sender="booc.class@gmail.com",
                to="thomathom@gmail.com",
                subject="Done updating notifications",
                body="Yeah buddy!")



the_job = NotificationNoAutoNowJob
