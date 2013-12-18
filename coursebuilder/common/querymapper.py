from google.appengine.ext import deferred, db
from google.appengine.runtime import DeadlineExceededError
import uuid
from webapp2 import cached_property
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
                result = self.map(entity)
                map_updates, map_deletes = result or ([], [])
                self.to_put.extend(map_updates)
                self.to_delete.extend(map_deletes)
                # Do updates and deletes in batches.
                if (i + 1) >= batch_size:
                    self._batch_write()
                    # Record the last entity we processed.
                    start_key = entity.key()
                    # Continue deferred...
                    raise DeadlineExceededError()
            self._batch_write()
        except DeadlineExceededError:
            # Write any unfinished updates to the datastore.
            # There is not enough time for this.
            #self._batch_write()
            # Queue a new task to pick up where we left off.
            deferred.defer(self._continue, start_key, batch_size)
            return
        deferred.defer(self._do_finish)

    def _do_finish(self):
        self.finish()
        self._batch_write()


class LogEntity(db.Model):
    messages = db.StringListProperty(indexed=False)
    sort_key = db.IntegerProperty()
    job_id = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)
    finished = db.BooleanProperty()


class LoggingMapper(Mapper):
    def __init__(self):
        super(LoggingMapper, self).__init__()
        self.log = []
        logging.debug('initializing LoggingMapper')
        self.log_number = 0
        self.job_id = str(uuid.uuid4())
        self.all_done = False

    def _batch_write(self):
        if self.log or self.all_done:
            entity = LogEntity(messages=self.log,
                        sort_key=self.log_number,
                        job_id=self.job_id,
                        finished=self.all_done)
            self.to_put.append(entity)
            self.log_number += 1
            self.log = []
        super(LoggingMapper, self)._batch_write()

    def _do_finish(self):
        self.all_done = True
        super(LoggingMapper, self)._do_finish()

    @classmethod
    def logs_for_job(cls, job_id):
        ents = LogEntity.all()
        ents.filter('job_id', job_id)
        ents.order('sort_key')

        for ent in ents:
            for message in ent.messages:
                yield message

    @classmethod
    def is_finished(cls, job_id):
        return bool(
                LogEntity.all().filter('job_id', job_id).filter('finished', True).count(limit=1))

    @classmethod
    def batch_count(cls, job_id, limit=50):
        return LogEntity.all().filter('job_id', job_id).count(limit=limit)

try:
    import cPickle as pickle
except ImportError:
    import pickle


class ObjLogEntity(db.Model):
    value = db.BlobProperty()
    sort_key = db.IntegerProperty()
    job_id = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now_add=True)
    finished = db.BooleanProperty()


class TableMakerMapper(Mapper):
    def __init__(self):
        super(TableMakerMapper, self).__init__()
        self._rows = []
        self.job_id = str(uuid.uuid4())
        self.finished = False
        self.part_number = 0

    def _batch_write(self):
        to_pickle = {
                'fields': self.FIELDS,
                'rows': self._rows,
                }
        entity = ObjLogEntity(
                value = pickle.dumps(to_pickle),
                sort_key = self.part_number,
                finished = self.finished,
                job_id = self.job_id,
                )
        self.to_put.append(entity)
        super(TableMakerMapper, self)._batch_write()
        self.part_number += 1
        self._rows = []

    def add_row(self, row):
        if not isinstance(row, dict):
            raise ValueError('Rows must be dicts')
        self._rows.append(row)

    def _do_finish(self):
        self.finished = True
        super(TableMakerMapper, self)._do_finish()


class TableMakerResult(object):
    def __init__(self, job_id):
        self.job_id = job_id

    def _query(self):
        return ObjLogEntity.all().filter('job_id', self.job_id).order('sort_key')

    @cached_property
    def fields(self):
        batch0 = self._query().get()
        if not batch0:
            raise Exception("No batches are done yet, can't determine fields.")
        return pickle.loads(batch0.value)['fields']

    @property
    def is_finished(self):
        q = self._query()
        q.filter('finished', True)
        return bool(q.count(limit=1))

    @property
    def batch_count(self, limit=50):
        q = self._query()
        return q.count(limit=limit)

    def __iter__(self):
        for ent in self._query():
            if ent.value:
                for row in pickle.loads(ent.value)['rows']:
                    yield row
