from google.appengine.ext import ndb

import re

def memodict(f):
  class memodict(dict):
    def __missing__(self, key):
      ret = self[key] = f(key)
      return ret 
  return memodict().__getitem__


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


class ServiceType(Enum):
  MEAL = 1
  FREE_FOOD = 2


class LatLong:
  def __init__(self, lat, lon):
    self.lat = lat
    self.lon = lon

  def to_geo(self):
    return ndb.GeoPt(self.lat, self.lon)

  @classmethod
  def to_geo(cls, latlong):
    return latlong and latlong.to_geo() or None

  @classmethod
  def from_geo(cls, geopt):
    return geopt and LatLong(geopt.lat, geopt.lon) or None

  @classmethod
  def from_str(cls, s):
    coords = [float(d) for d in re.split(r'[, ]+', s) if d]
    if len(coords) == 2:
      return LatLong(*coords)


class SearchResult:
  def __init__(self, name, address, location=None, phones=[], website=None):
    self.id = None
    self.name = name
    self.address = address
    self.location = location
    self.phones = phones
    self.website = website


class Field:
  LOCATION = 'LOCATION'
  SIXTY_PLUS = 'SIXTY_PLUS'
  ACCESSIBLE = 'ACCESSIBLE'


class Query:
  def __init__(self):
    self.filters = {}

  def add_filter(self, field, value):
    self.filters[field] = value

  def get(self, field):
    return self.filters[field]


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

