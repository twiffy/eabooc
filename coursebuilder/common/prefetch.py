from webapp2 import cached_property
from models.models import MemcacheManager
from google.appengine.ext import db
import logging
def prefetch_refprops(entities, *props):
    fields = [(entity, prop) for entity in entities for prop in props]
    ref_keys = [prop.get_value_for_datastore(x) for x, prop in fields]
    ref_entities = dict((x.key(), x) for x in db.get(set(ref_keys)))
    for (entity, prop), ref_key in zip(fields, ref_keys):
        prop.__set__(entity, ref_entities[ref_key])
    return entities

NO_OBJECT = object()

class CachingPrefetcher(object):
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

