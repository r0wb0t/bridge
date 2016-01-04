from google.appengine.ext import ndb
from query import ServiceType


class EnumProperty(ndb.IntegerProperty):
  def __init__(self, enum_type, **kwargs):
    super(EnumProperty, self).__init__(choices=enum_type.values(), **kwargs)
    self.enum_type = enum_type

  def _validate(self, value):
    super(EnumProperty, self)._validate(value.number)

  def _to_base_type(self, value):
    return value.number

  def _from_base_type(self, value):
    return self.enum_type.for_number(value)


class KioskLocation(ndb.Model):
  name = ndb.StringProperty()
  address = ndb.TextProperty()
  location = ndb.GeoPtProperty()


class ServiceTime(ndb.Model):
  start = ndb.TimeProperty()
  end = ndb.TimeProperty()
  days = ndb.IntegerProperty(repeated=True)
  only_dates = ndb.DateProperty(repeated=True)
  not_dates = ndb.DateProperty(repeated=True)


class Service(ndb.Model):
  service_id = ndb.IntegerProperty()

  service_type = EnumProperty(ServiceType)
  service_detail = ndb.StringProperty()

  times = ndb.LocalStructuredProperty(ServiceTime, repeated=True)
  not_dates = ndb.DateProperty(repeated=True)

  requires_ticket = ndb.BooleanProperty()
  requires_local_addr = ndb.BooleanProperty()
  requires_church_attend = ndb.BooleanProperty()
  sixty_plus = ndb.BooleanProperty()

  extra_notes = ndb.TextProperty()


class Location(ndb.Model):
  org_name = ndb.StringProperty()

  name = ndb.StringProperty()
  address = ndb.TextProperty()
  geo = ndb.GeoPtProperty()
  phones = ndb.IntegerProperty(repeated=True)
  websites = ndb.StringProperty(repeated=True)

  services = ndb.LocalStructuredProperty(Service, repeated=True)

  accessible = ndb.BooleanProperty()
  extra_notes = ndb.TextProperty()

  last_modified = ndb.DateTimeProperty(auto_now=True)

  def service(self, service_id):
    for service in self.services:
      if service.service_id == service_id:
        return service

  def add_service(self):
    service = Service()
    if self.services:
      service.service_id = max(s.service_id for s in self.services) + 1
    else:
      service.service_id = 1
    self.services.append(service)
    return service

