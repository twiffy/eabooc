from google.appengine.ext import deferred
from google.appengine.runtime import DeadlineExceededError

# straight from google
class Mapper(object):
    # Subclasses should replace this with a model class (eg, model.Person).
    KIND = None

    # Subclasses can replace this with a list of (property, value) tuples to filter by.
    FILTERS = []

    def __init__(self):
        self.to_put = []
        self.to_delete = []

    def map(self, entity):
        """Updates a single entity.

        Implementers should return a tuple containing two iterables (to_update, to_delete).
        """
        return ([], [])

    def finish(self):
        """Called when the mapper has finished, to allow for any final work to be done."""
        pass

    def get_query(self):
        """Returns a query over the specified kind, with any appropriate filters applied."""
        q = self.KIND.all()
        for prop, value in self.FILTERS:
            q.filter("%s =" % prop, value)
        q.order("__key__")
        return q

    def run(self, batch_size=100):
        """Starts the mapper running."""
        self._continue(None, batch_size)

    def _batch_write(self):
        """Writes updates and deletes entities in a batch."""
        if self.to_put:
            db.put(self.to_put)
            self.to_put = []
        if self.to_delete:
            db.delete(self.to_delete)
            self.to_delete = []

    def _continue(self, start_key, batch_size):
        q = self.get_query()
        # If we're resuming, pick up where we left off last time.
        if start_key:
            q.filter("__key__ >", start_key)
        # Keep updating records until we run out of time.
        try:
            # Steps over the results, returning each entity and its index.
            for i, entity in enumerate(q):
                map_updates, map_deletes = self.map(entity)
                self.to_put.extend(map_updates)
                self.to_delete.extend(map_deletes)
                # Do updates and deletes in batches.
                if (i + 1) % batch_size == 0:
                    self._batch_write()
                # Record the last entity we processed.
                start_key = entity.key()
            self._batch_write()
        except DeadlineExceededError:
            # Write any unfinished updates to the datastore.
            self._batch_write()
            # Queue a new task to pick up where we left off.
            deferred.defer(self._continue, start_key, batch_size)
            return
        self.finish()


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


the_job = WikisDraftJob
