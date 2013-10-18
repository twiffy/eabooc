from google.appengine.ext import deferred, db
from google.appengine.runtime import DeadlineExceededError
from google.appengine.api.datastore.datastore_errors import Timeout
import uuid
import logging

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
        except DeadlineExceededError, Timeout:
            # Write any unfinished updates to the datastore.
            # There is not enough time for this.
            #self._batch_write()
            # Queue a new task to pick up where we left off.
            deferred.defer(self._continue, start_key, batch_size)
            return
        deferred.defer(self.finish)


class LogEntity(db.Model):
    messages = db.StringListProperty(indexed=False)
    sort_key = db.IntegerProperty()
    job_id = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)


class LoggingMapper(Mapper):
    def __init__(self):
        super(LoggingMapper, self).__init__()
        self.log = []
        logging.debug('initializing LoggingMapper')
        self.log_number = 0
        self.job_id = str(uuid.uuid4())

    def _batch_write(self):
        if self.log:
            self.to_put.append(
                    LogEntity(messages=self.log,
                        sort_key=self.log_number,
                        job_id=self.job_id))
            self.log_number += 1
            self.log = []
        super(LoggingMapper, self)._batch_write()

    @classmethod
    def logs_for_job(cls, job_id):
        ents = LogEntity.all()
        ents.filter('job_id', job_id)
        ents.order('sort_key')

        for ent in ents:
            for message in ent.messages:
                yield message
