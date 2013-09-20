# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Core data model classes."""

__author__ = 'Pavel Simakov (psimakov@google.com)'

import logging
import appengine_config
from config import ConfigProperty
import counters
from counters import PerfCounter
from entities import BaseEntity
import transforms
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.ext import deferred

import hashlib
import random

# We want to use memcache for both objects that exist and do not exist in the
# datastore. If object exists we cache its instance, if object does not exist
# we cache this object below.
NO_OBJECT = {}

# The default amount of time to cache the items for in memcache.
DEFAULT_CACHE_TTL_SECS = 60 * 5

# Global memcache controls.
CAN_USE_MEMCACHE = ConfigProperty(
    'gcb_can_use_memcache', bool, (
        'Whether or not to cache various objects in memcache. For production '
        'this value should be on to enable maximum performance. For '
        'development this value should be off so you can see your changes to '
        'course content instantaneously.'),
    appengine_config.PRODUCTION_MODE)

# performance counters
CACHE_PUT = PerfCounter(
    'gcb-models-cache-put',
    'A number of times an object was put into memcache.')
CACHE_HIT = PerfCounter(
    'gcb-models-cache-hit',
    'A number of times an object was found in memcache.')
CACHE_MISS = PerfCounter(
    'gcb-models-cache-miss',
    'A number of times an object was not found in memcache.')
CACHE_DELETE = PerfCounter(
    'gcb-models-cache-delete',
    'A number of times an object was deleted from memcache.')


class MemcacheManager(object):
    """Class that consolidates all memcache operations."""

    @classmethod
    def get(cls, key, namespace=None):
        """Gets an item from memcache if memcache is enabled."""
        #logging.debug("MemcacheManager:get(%s, ns=%s)", key, namespace)
        if not CAN_USE_MEMCACHE.value:
            return None
        if not namespace:
            namespace = appengine_config.DEFAULT_NAMESPACE_NAME
        value = memcache.get(key, namespace=namespace)

        # We store some objects in memcache that don't evaluate to True, but are
        # real objects, '{}' for example. Count a cache miss only in a case when
        # an object is None.
        if value != None:  # pylint: disable-msg=g-equals-none
            #logging.debug('Cache HIT, key: %s. %s', key, Exception())
            CACHE_HIT.inc()
        else:
            logging.info('Cache miss, key: %s. %s', key, Exception())
            CACHE_MISS.inc(context=key)
        return value

    @classmethod
    def set(cls, key, value, ttl=DEFAULT_CACHE_TTL_SECS, namespace=None):
        """Sets an item in memcache if memcache is enabled."""
        #logging.debug("MemcacheManager:set(%s, (val), ns=%s)", key, namespace)
        if CAN_USE_MEMCACHE.value:
            CACHE_PUT.inc()
            if not namespace:
                namespace = appengine_config.DEFAULT_NAMESPACE_NAME
            memcache.set(key, value, ttl, namespace=namespace)

    @classmethod
    def incr(cls, key, delta, namespace=None):
        """Incr an item in memcache if memcache is enabled."""
        #logging.debug("MemcacheManager:incr(%s, %s, ns=%s)", key, str(delta), namespace)
        if CAN_USE_MEMCACHE.value:
            if not namespace:
                namespace = appengine_config.DEFAULT_NAMESPACE_NAME
            memcache.incr(key, delta, namespace=namespace, initial_value=0)

    @classmethod
    def delete(cls, key, namespace=None):
        """Deletes an item from memcache if memcache is enabled."""
        #logging.debug("MemcacheManager:delete(%s, ns=%s)", key, namespace)
        if CAN_USE_MEMCACHE.value:
            CACHE_DELETE.inc()
            if not namespace:
                namespace = appengine_config.DEFAULT_NAMESPACE_NAME
            memcache.delete(key, namespace=namespace)


CAN_AGGREGATE_COUNTERS = ConfigProperty(
    'gcb_can_aggregate_counters', bool,
    'Whether or not to aggregate and record counter values in memcache. '
    'This allows you to see counter values aggregated across all frontend '
    'application instances. Without recording, you only see counter values '
    'for one frontend instance you are connected to right now. Enabling '
    'aggregation improves quality of performance metrics, but adds a small '
    'amount of latency to all your requests.',
    default_value=False)


def incr_counter_global_value(name, delta):
    if CAN_AGGREGATE_COUNTERS.value:
        MemcacheManager.incr('counter:' + name, delta)


def get_counter_global_value(name):
    if CAN_AGGREGATE_COUNTERS.value:
        return MemcacheManager.get('counter:' + name)
    else:
        return None

counters.get_counter_global_value = get_counter_global_value
counters.incr_counter_global_value = incr_counter_global_value

class MoreDifferentIntListProperty(db.Property):
    data_type = list
    def validate(self, value):
        if value is None:
            return []
        if type(value) is not list:
            raise ValueError("Expected list, got %s", type(value).__name__)
        return value

    def get_value_for_datastore(self, model):
        py_value = super(MoreDifferentIntListProperty, self).get_value_for_datastore(model)
        if py_value is None:
            py_value = []
        return transforms.dumps(py_value)

    def make_value_from_datastore(self, db_value):
        logging.debug("Getting from db: have value %s", repr(db_value))
        if type(db_value) is list:
            return db_value
        elif not db_value:
            return []
        return transforms.loads(db_value)

    def make_value_from_datastore_index_value(self, i_value):
        logging.debug("What is an index value? %s", repr(i_value))
        return self.make_value_from_datastore(i_value)


class Student(BaseEntity):
    """Student profile."""
    enrolled_on = db.DateTimeProperty(auto_now_add=True, indexed=True)
    user_id = db.StringProperty(indexed=True)
    name = db.StringProperty()
    is_enrolled = db.BooleanProperty()
    wiki_id = db.IntegerProperty()

    # Each of the following is a string representation of a JSON dict.
    scores = db.TextProperty(indexed=False)

    # --- Additional fields for Assessment BOOC ---

    # If the student is able to use the wiki, comment, etc.
    is_participant = db.BooleanProperty()

    # The lat/longitude, and name, of the student's location
    location_city = db.StringProperty(indexed=False)
    location_state = db.StringProperty(indexed=False)
    location_country = db.StringProperty(indexed=False)

    # The user's education level.  Maximum or in-progress?
    education_level = db.StringProperty(indexed=False)

    # The student's primary role in the education system
    # (instructor, administrator, researcher?)
    role = db.StringProperty(indexed=False)

    # Other registration questions
    # Not indexed because String List Properties multiply
    # the number of writes by a lot!  But also we don't
    # need these indexes yet; if we do, that's ok.
    grade_levels = db.StringListProperty(indexed=False)
    title_and_setting = db.StringListProperty(indexed=False)
    faculty_area = db.StringListProperty(indexed=False)
    student_subject = db.StringListProperty(indexed=False)
    research_area = db.StringListProperty(indexed=False)
    other_role = db.StringProperty(indexed=False)

    # deprecated...
    notifications = db.StringListProperty(indexed=False)

    is_teaching_assistant = db.BooleanProperty(default=False)
    group_id = db.StringProperty(indexed=True)

    wikis_posted = MoreDifferentIntListProperty()

    _memcache_ids = set(('email', 'wiki_id'))

    def __init__(self, *args, **kwargs):
        super(Student, self).__init__(*args, **kwargs)

    def ensure_wiki_id(self):
        if not self.wiki_id:
            # Only has key, not necessarily anything else.
            digest = hashlib.sha256(str(self.key())).hexdigest()
            wiki_id = int(digest[0:4], 16)
            while Student.all().filter('wiki_id =', wiki_id).count(limit=1) > 0:
                logging.info('Wiki_id collision for %s: %d, re-rolling.', self.key().name(), wiki_id)
                wiki_id += random.randrange(100)
            self.wiki_id = wiki_id

    @classmethod
    def _memcache_key(cls, key, by='email'):
        """Makes a memcache key from primary key or other unique id."""
        if by not in cls._memcache_ids:
            raise ValueError('Can only memcache by unique values')
        return 'entity:student-by-%s:%s' % (by, key)

    def set_profile_pic(self, orig_filename, image_data):
        """Set the user's profile picture."""
        # TODO: maybe use the blobstore to work with images.
        image = images.Image(image_data=image_data)
        # TODO: maybe async. Maybe make an ImageProperty descriptor thing.
        image.resize(width=100, height=100)
        self.profile_pic = image.execute_transforms(
                output_encoding=images.JPEG)

    def put(self):
        """Do the normal put() and also add the object to memcache."""
        self.ensure_wiki_id()
        result = super(Student, self).put()
        MemcacheManager.set(self._memcache_key(self.key().name()), self, ttl=60*60*12)
        MemcacheManager.set(self._memcache_key(self.wiki_id, by='wiki_id'), self, ttl=60*60*12)
        return result

    def delete(self):
        """Do the normal delete() and also remove the object from memcache."""
        super(Student, self).delete()
        MemcacheManager.delete(self._memcache_key(self.key().name()))
        MemcacheManager.delete(self._memcache_key(self.wiki_id, by='wiki_id'))

    @classmethod
    def get_by_email(cls, email):
        return Student.get_by_key_name(email.encode('utf8'))

    @classmethod
    def get_enrolled_student_by_email(cls, email):
        """Returns enrolled student or None."""
        student = MemcacheManager.get(cls._memcache_key(email))
        if NO_OBJECT == student:
            return None
        if not student:
            student = Student.get_by_email(email)
            if student:
                MemcacheManager.set(cls._memcache_key(email), student, ttl=60*60*12)
            else:
                MemcacheManager.set(cls._memcache_key(email), NO_OBJECT)
        if student and student.is_enrolled:
            return student
        else:
            return None

    @classmethod
    def get_enrolled_student_by_wiki_id(cls, wiki_id):
        student = MemcacheManager.get(cls._memcache_key(wiki_id, by='wiki_id'))
        if NO_OBJECT == student:
            return None
        if not student:
            student = Student.get_by_wiki_id(wiki_id)
            if student:
                MemcacheManager.set(cls._memcache_key(wiki_id, by='wiki_id'), student, ttl=60*60*12)
            else:
                MemcacheManager.set(cls._memcache_key(wiki_id, by='wiki_id'), NO_OBJECT)
        if student and student.is_enrolled:
            return student
        else:
            return None

    @classmethod
    def get_by_wiki_id(cls, wiki_id):
        student = (Student.all()
            .filter("wiki_id =", wiki_id)
            .get())
        return student

    @classmethod
    def rename_current(cls, new_name):
        """Gives student a new name."""
        user = users.get_current_user()
        if not user:
            raise Exception('No current user.')
        if new_name:
            student = Student.get_by_email(user.email())
            if not student:
                raise Exception('Student instance corresponding to user %s not '
                                'found.' % user.email())
            student.name = new_name
            student.put()

    @classmethod
    def set_enrollment_status_for_current(cls, is_enrolled):
        """Changes student enrollment status."""
        user = users.get_current_user()
        if not user:
            raise Exception('No current user.')
        student = Student.get_by_email(user.email())
        if not student:
            raise Exception('Student instance corresponding to user %s not '
                            'found.' % user.email())
        student.is_enrolled = is_enrolled
        student.put()

    def get_key(self):
        if not self.user_id:
            raise Exception('Student instance has no user_id set.')
        return db.Key.from_path(Student.kind(), self.user_id)

    @classmethod
    def get_student_by_user_id(cls, user_id):
        students = cls.all().filter(cls.user_id.name, user_id).fetch(limit=2)
        if len(students) == 2:
            raise Exception(
                'There is more than one student with user_id %s' % user_id)
        return students[0] if students else None

    def has_same_key_as(self, key):
        """Checks if the key of the student and the given key are equal."""
        return key == self.get_key()


class EventEntity(BaseEntity):
    """Generic events.

    Each event has a 'source' that defines a place in a code where the event was
    recorded. Each event has a 'user_id' to represent an actor who triggered
    the event. The event 'data' is a JSON object, the format of which is defined
    elsewhere and depends on the type of the event.
    """
    recorded_on = db.DateTimeProperty(auto_now_add=True, indexed=True)
    source = db.StringProperty(indexed=False)
    user_id = db.StringProperty(indexed=False)

    # Each of the following is a string representation of a JSON dict.
    data = db.TextProperty(indexed=False)

    @classmethod
    def record(cls, source, user, data):
        """Records new event into a datastore."""

        event = EventEntity()
        event.source = source
        event.user_id = user.user_id()
        event.data = data
        event.put()


class StudentAnswersEntity(BaseEntity):
    """Student answers to the assessments."""

    updated_on = db.DateTimeProperty(indexed=True)

    # Each of the following is a string representation of a JSON dict.
    data = db.TextProperty(indexed=False)


class StudentPropertyEntity(BaseEntity):
    """A property of a student, keyed by the string STUDENT_ID-PROPERTY_NAME."""

    updated_on = db.DateTimeProperty(indexed=True)

    name = db.StringProperty()
    # Each of the following is a string representation of a JSON dict.
    value = db.TextProperty()

    @classmethod
    def _memcache_key(cls, key):
        """Makes a memcache key from primary key."""
        return 'entity:student_property:%s' % key

    @classmethod
    def create_key(cls, student_id, property_name):
        return '%s-%s' % (student_id, property_name)

    @classmethod
    def create(cls, student, property_name):
        return StudentPropertyEntity(
            key_name=cls.create_key(student.user_id, property_name),
            name=property_name)

    def put(self):
        """Do the normal put() and also add the object to memcache."""
        result = super(StudentPropertyEntity, self).put()
        MemcacheManager.set(self._memcache_key(self.key().name()), self)
        return result

    def delete(self):
        """Do the normal delete() and also remove the object from memcache."""
        super(Student, self).delete()
        MemcacheManager.delete(self._memcache_key(self.key().name()))

    @classmethod
    def get(cls, student, property_name):
        """Loads student property."""
        key = cls.create_key(student.user_id, property_name)
        value = MemcacheManager.get(cls._memcache_key(key))
        if NO_OBJECT == value:
            return None
        if not value:
            value = cls.get_by_key_name(key)
            if value:
                MemcacheManager.set(cls._memcache_key(key), value)
            else:
                MemcacheManager.set(cls._memcache_key(key), NO_OBJECT)
        return value
