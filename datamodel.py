from datetime import datetime, timedelta

from google.appengine.ext import ndb
from protorpc import messages, message_types

import re

def memoize(f):
  m = {}
  def get(*args):
    if args not in m:
      m[args] = f(*args)
    return m[args]
  return get

class EnumType(type):
  def __init__(cls, name, bases, dct):
    super(EnumType, cls).__init__(name, bases, dct)
    cls._reverse_dict = {}
    for k, v in cls.__dict__.items():
      if not k.startswith('_') and type(v) == int:
        instance = cls()
        instance.name = k
        instance.number = v
        setattr(cls, k, instance) 
        cls._reverse_dict[v] = instance


class Enum(object):
  __metaclass__ = EnumType

  @classmethod
  def values(enum_type):
    return [v for k, v in enum_type.__dict__.items()
              if not k.startswith('_')]

  @classmethod
  def names(enum_type):
    return [k for k, v in enum_type.__dict__.items()
              if not k.startswith('_')]

  @classmethod
  def for_name(enum_type, name):
    return enum_type.__dict__[name]

  @classmethod
  def for_number(enum_type, number):
    return enum_type._reverse_dict[number]

  @classmethod
  def export_to(enum_type, jinja_env):
    jinja_env.globals[enum_type.__name__] = enum_type


class DataObjectMeta(type):
  def __init__(cls, name, bases, dct):
    if 'DataObject' in globals():
      assert bases == (DataObject,), cls
      assert cls.Storage.__bases__ == (messages.Message,), cls

    super(DataObjectMeta, cls).__init__(name, bases, dct)


class DataObject(object):
  __metaclass__ = DataObjectMeta

  def __init__(self, **kwargs):
    self._storage = self.__class__.Storage(**kwargs)

  def __getattr__(self, name):
    if '_storage' in self.__dict__ and name in self.__class__.Storage.__dict__:
      return getattr(self._storage, name)

  def __setattr__(self, name, value):
    if '_storage' in self.__dict__ and name in self.__class__.Storage.__dict__:
      return setattr(self._storage, name, value)
    object.__setattr__(self, name, value)

  def get_message(self):
    return self._storage


class ServiceType(Enum):
  MEAL = 1
  FREE_FOOD = 2


class UserProfile(messages.Message):
  user_id = messages.StringField(1, required=True)

  is_admin = messages.BooleanField(2, default=False)
  wants_admin = messages.BooleanField(3, default=False)

  email = messages.StringField(4, required=False)


class AdminInvite(messages.Message):
  id = messages.IntegerField(2)
  code = messages.StringField(1, required=True)


class LogItemType(messages.Enum):
  UNKNOWN = 0
  NOTE = 1
  DELTA = 2


class LogItem(DataObject):
  class Storage(messages.Message):
    timestamp = message_types.DateTimeField(2)
    user_id = messages.StringField(6)
    flag = messages.BooleanField(7)

    type = messages.EnumField(LogItemType, 3)

    class Note(messages.Message):
      text = messages.StringField(1)
      category = messages.StringField(2)
    note = messages.MessageField(Note, 4)

    class Delta(messages.Message):
      path = messages.StringField(1)
      string_val = messages.StringField(2)
    delta = messages.MessageField(Delta, 5)

  log_for = [] # ForeignKey


class Time(messages.Message):
  hour = messages.IntegerField(1)
  minute = messages.IntegerField(2)


class Service(messages.Message):
  id = messages.IntegerField(1)

  class Type(messages.Enum):
    UNKNOWN = 0
    MEAL = 1
    FREE_FOOD = 2
  service_type = messages.EnumField(Type, 2)

  service_detail = messages.StringField(3)

  class ServiceTime(messages.Message):
    day = messages.IntegerField(1, required=True)
    start = messages.MessageField(Time, 2, required=True)
    end = messages.MessageField(Time, 3)
  times = messages.MessageField(ServiceTime, 4, repeated=True)

  class ServiceNotDate(messages.Message):
    month = messages.IntegerField(1)
    day = messages.IntegerField(2)
  not_dates = messages.MessageField(ServiceNotDate, 5, repeated=True)

  requires_ticket = messages.BooleanField(6)
  requires_local_addr = messages.BooleanField(7)
  requires_church_attend = messages.BooleanField(8)
  sixty_plus = messages.BooleanField(9)

  extra_notes = messages.StringField(10)


class ServicePhone(messages.Message):
  number = messages.StringField(1)
  days = messages.IntegerField(2, repeated=True)
  start = messages.MessageField(Time, 3)
  end = messages.MessageField(Time, 4)

  
class LatLong(DataObject):
  class Storage(messages.Message):
    lat = messages.FloatField(1)
    lon = messages.FloatField(2)

  def geo(self):
    return ndb.GeoPt(self.lat, self.lon)

  @classmethod
  def to_geo(cls, latlong):
    return latlong and latlong.geo() or None

  @classmethod
  def from_geo(cls, geopt):
    return geopt and LatLong(lat=geopt.lat, lon=geopt.lon) or None

  @classmethod
  def from_str(cls, s):
    coords = [float(d) for d in re.split(r'[, ]+', s) if d]
    if len(coords) == 2:
      return LatLong(lat=coords[0], lon=coords[1])


class Location(messages.Message):
  id = messages.IntegerField(1)

  org_name = messages.StringField(2)

  name = messages.StringField(3)
  address = messages.StringField(4)
  geo = messages.MessageField(LatLong.Storage, 5)
  phone = messages.MessageField(ServicePhone, 6)
  websites = messages.StringField(7, repeated=True)

  accessible = messages.BooleanField(8)
  extra_notes = messages.StringField(9)

  last_modified = message_types.DateTimeField(10)


class SearchContext(object):
  def __init__(self, now):
    self.now = now


class SearchSection(messages.Enum):
  TODAY = 0
  TOMORROW = 1
  LATER = 2  


class SearchResult(object):
  def __init__(self, context, name, address, location=None, phones=[], website=None):
    self.context = context
    self.id = None
    self.name = name
    self.address = address
    self.location = location
    self.phones = phones
    self.website = website

  @memoize
  def days(self):
    return set((service_time.day
        for service_time in self.service_times
        if service_time.day is not None))

  @memoize
  def section(self):
    if self.context.now.weekday() in self.days():
      return SearchSection.TODAY
    return SearchSection.LATER


class Field:
  LOCATION = 'LOCATION'
  SIXTY_PLUS = 'SIXTY_PLUS'
  ACCESSIBLE = 'ACCESSIBLE'
  LOCATION_ID = 'LOCATION_ID'


class Query:
  def __init__(self):
    self.filters = {}

  def add_filter(self, field, value):
    self.filters[field] = value

  def get(self, field):
    return self.filters.get(field)


class Ranker(object):
  def __init__(self, query):
    self.query = query
    self.now = datetime.now() - timedelta(hours=8)

  def rerank(self, results):
    results = list(results)
    results.sort(key=self.score)
    return results

  def score(self, result):
    return self.dayscore(result)

  def dayscore(self, result):
    if len(result.days()) == 0:
      return 10
    return min((day - self.now.weekday()) % 7 for day in result.days()) / 7.0

  def timescore(self, result):
    return result. min()


# Backends.
#
# Backends must implement a .search(query) method.

class OhanaBackend:
  def __init__(self, ohana):
    self.ohana = ohana

  def search(self, query):
    params = {'keywords': 'food'}
    location = query.get(Field.LOCATION) 
    if location is not None:
      params['latitude'] = location.lat
      params['longitude'] = location.lon

    return [self.make_result(loc) for loc in self.ohana.search(**params)]

  def make_result(self, loc):
    return SearchResult(name=loc.name,
                        address=str(loc.address),
                        location=LatLong(loc.latitude, loc.longitude),
                        website=loc.website)

