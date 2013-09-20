from google.appengine.ext import db
import logging
def prefetch_refprops(entities, *props):
    fields = [(entity, prop) for entity in entities for prop in props]
    ref_keys = [prop.get_value_for_datastore(x) for x, prop in fields]
    ref_entities = dict((x.key(), x) for x in db.get(set(ref_keys)))
    for (entity, prop), ref_key in zip(fields, ref_keys):
        prop.__set__(entity, ref_entities[ref_key])
    return entities

class CachingPrefetcher(object):
    def __init__(self):
        self.cache = {}

    def add(self, obj):
        self.cache[obj.key()] = obj

    def prefetch(self, entities_iterable, *props):
        entities = list(entities_iterable)
        if len(entities) == 0:
            return entities
        fields = [(entity, prop) for entity in entities for prop in props]
        #logging.warning('there are %d (%d) entities of type %s',
                #len(entities),
                #len(fields),
                #type(entities[0]).__name__)
        ref_keys = [prop.get_value_for_datastore(x) for x, prop in fields]
        ref_key_set = set(ref_keys) - set((None,))
        keys_to_fetch = ref_key_set - self.cache.viewkeys()

        if keys_to_fetch:
            #logging.warning('fetching %d entities on type %s', len(keys_to_fetch), type(entities[0]).__name__)
            ref_entities = dict((x.key(), x) for x in db.get(keys_to_fetch))
            self.cache.update(ref_entities)
        #else:
            #logging.warning('Not fetching any entities for %s, they all cached bro', type(entities[0]).__name__)
        for (entity, prop), ref_key in zip(fields, ref_keys):
            prop.__set__(entity, self.cache[ref_key])

        return entities
