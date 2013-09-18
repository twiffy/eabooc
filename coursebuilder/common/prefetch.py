from google.appengine.ext import db
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

    def prefetch(self, entities, *props):
        fields = [(entity, prop) for entity in entities for prop in props]
        ref_keys = set([prop.get_value_for_datastore(x) for x, prop in fields])
        keys_to_fetch = ref_keys - self.cache.viewkeys()

        if keys_to_fetch:
            ref_entities = dict((x.key(), x) for x in db.get(keys_to_fetch))
            self.cache.update(ref_entities)

        for (entity, prop), ref_key in zip(fields, ref_keys):
            prop.__set__(entity, self.cache[ref_key])
        return entities
