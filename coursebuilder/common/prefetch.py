"""
prefetch.py - functions for speeding up the fetching of objects from
the datastore.

The datastore is super slow.  But it's much slower in latency than
it is in read speed once you've got a query going.

"""
from webapp2 import cached_property
from models.models import MemcacheManager
from google.appengine.ext import db
import logging


def prefetch_refprops(entities, *props):
    """
    Given some datastore model objects, and some ReferenceProperties
    (ModelClass.property rather than model_object.property),
    fetch all the referenced objects at once, to avoid a situation
    where they are fetched one at a time, with tons of latency.

    http://blog.notdot.net/2010/01/ReferenceProperty-prefetching-in-App-Engine
    """
    fields = [(entity, prop) for entity in entities for prop in props]
    ref_keys = [prop.get_value_for_datastore(x) for x, prop in fields]
    ref_entities = dict((x.key(), x) for x in db.get(set(ref_keys)))
    for (entity, prop), ref_key in zip(fields, ref_keys):
        prop.__set__(entity, ref_entities[ref_key])
    return entities

NO_OBJECT = object()

class CachingPrefetcher(object):
    """
    Loosely based on prefetch_refprops above, this prefetcher
    keeps track of all the entities that will need to fetched
    to render an entire page - comments, page and comment authors,
    etc.

    I tried really hard to use memcached for more, but it's
    just so hard to keep the cache updated in all the situations
    where the underlying data changes.  I gave up and worked
    on just fetching datastore items with as little latency
    as possible.
    """
    def __init__(self, top_key=None, already_have=[]):
        self.top_key = top_key
        self.cache = { x.key(): x for x in already_have }
        self.prefetch_query = None
        self.new_keys_fetched = False
        if top_key:
            keys_to_prefetch = MemcacheManager.get(self._collection_key)
            if keys_to_prefetch:
                keys_to_prefetch = set(keys_to_prefetch).difference(map(str, self.cache.keys()))
                self.prefetch_query = db.get_async(keys_to_prefetch)
            else:
                self.new_keys_fetched = len(already_have) > 0

    @cached_property
    def _collection_key(self):
        return 'cached-things-by-page:%s' % self.top_key

    def add(self, obj):
        self.cache[obj.key()] = obj

    def prefetch(self, entities_iterable, *props):
        if self.prefetch_query:
            try:
                self.cache.update(
                        { x.key(): x for x in self.prefetch_query.get_result() })
                self.prefetch_query = None
            except Exception:
                logging.exception('Error in preemptive prefetch')
                # Couldn't get the data from the preemptive query, so let's discard that query.
                self.prefetch_query = None
                self.cache = {}
                self.new_keys_fetched = True

        entities = list(entities_iterable)
        if len(entities) == 0:
            return entities
        try:
            fields = [(entity, prop) for entity in entities for prop in props]
            #logging.warning('there are %d (%d) entities of type %s',
                    #len(entities),
                    #len(fields),
                    #type(entities[0]).__name__)
            ref_keys = [prop.get_value_for_datastore(x) for x, prop in fields]
            ref_key_set = set(ref_keys)
            ref_key_set.discard(None)
            keys_to_fetch = ref_key_set - self.cache.viewkeys()

            if keys_to_fetch:
                #logging.warning('fetching %d entities on type %s', len(keys_to_fetch), type(entities[0]).__name__)
                ref_entities = dict((x.key(), x) for x in db.get(keys_to_fetch) if x)
                self.cache.update(ref_entities)
                self.new_keys_fetched = True
            #else:
                #logging.warning('Not fetching any entities for %s, they all cached bro', type(entities[0]).__name__)
            for (entity, prop), ref_key in zip(fields, ref_keys):
                if ref_key is not None:
                    val = self.cache.get(ref_key, NO_OBJECT)
                    if val is not NO_OBJECT:
                        prop.__set__(entity, val)
        except:
            logging.exception('Error in prefetch')

        # Always return entities, even if there was a problem
        return entities

    def done(self):
        if self.new_keys_fetched:
            MemcacheManager.set(
                    self._collection_key,
                    list(str(x) for x in self.cache.keys()),
                    ttl=60*60*48)

def ensure_key(it):
    """
    Turn something into a db.Key.

    Currently handles keys, strings that encode keys,
    and model objects.
    """
    key = None
    if isinstance(it, db.Key):
        key = it
    elif isinstance(it, basestring):
        key = db.Key(it)
    elif hasattr(it, 'key'):
        key = it.key()
    else:
        raise ValueError(
                'Expects argument to be a Model or Key; received %s (a %s).' %
                (arg, typename(arg)))

    assert isinstance(key, db.Key)
    if not key.has_id_or_name():
        raise ValueError('Key %r is not complete.' % key)

    return key
