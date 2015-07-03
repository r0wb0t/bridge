

class LatLong:
  def __init__(self, lat, lon):
    self.lat = lat
    self.lon = lon

  @classmethod
  def from_str(cls, s):
    return LatLong(*[float(d) for d in s.split(',')])


class SearchResult:
  def __init__(self, name, address, location=None, phones=[], website=None):
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
    

class AppEngineBackend:
  def search(self, query):
    q = FoodSource.query()
    # TODO(rnairn): Add filters etc.
    return list(q)
