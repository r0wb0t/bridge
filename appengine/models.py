from datetime import datetime
from itertools import groupby

from google.appengine.ext import ndb
from google.appengine.ext.ndb.msgprop import MessageProperty

import datamodel


def message_model(id_field=None, auto_now=[]):
  class Mixin:
    def _pre_put_hook(self):
      if id_field and self.key.id() is None and getattr(self.message, id_field) is not None:
        self.key = ndb.Key(UserProfile, getattr(self.message, id_field))

      for field in auto_now:
        setattr(self.message, field, datetime.utcnow())

    @classmethod
    def _post_get_hook(cls, key, future):
      obj = future.get_result()
      if obj:
        obj.populate_id()

    def populate_id(self):
      if id_field and getattr(self.message, id_field) is None:
        setattr(self.message, id_field, self.key.id())

    @classmethod
    def get_key(cls, message):
      assert id_field
      return ndb.Key(cls, getattr(message, id_field))
      
  return Mixin


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


class UserProfile(message_model(id_field='user_id'), ndb.Model):
  message = MessageProperty(
      datamodel.UserProfile,
      indexed_fields=['is_admin', 'wants_admin'])

  def _pre_put_hook(self):
    if self.key.id() is None:
      assert self.message.user_id
      self.key = ndb.Key(UserProfile, self.message.user_id)

  @staticmethod
  def for_user_id(user_id):
    '''A get_by_id that always returns a result.'''
    assert user_id
    stored = UserProfile.get_by_id(user_id)
    if stored is not None:
      return stored
    else:
      return UserProfile(
          id=user_id,
          message=datamodel.UserProfile(user_id=user_id))


class AdminInvite(message_model(id_field='id'), ndb.Model):
  message = MessageProperty(
      datamodel.AdminInvite,
      indexed_fields=['code'])


class LogItem(message_model(auto_now=['timestamp']), ndb.Model):
  message = MessageProperty(
      datamodel.LogItem.Storage)
 
  log_for = ndb.KeyProperty()
 

class KioskLocation(ndb.Model):
  name = ndb.StringProperty()
  address = ndb.TextProperty()
  location = ndb.GeoPtProperty()


class ServiceTime(ndb.Model):
  day = ndb.IntegerProperty(required=True)
  start = ndb.TimeProperty(required=True)
  end = ndb.TimeProperty()


class ServiceNotDate(ndb.Model):
  month = ndb.IntegerProperty()
  day = ndb.IntegerProperty()


class Service(ndb.Model):
  service_id = ndb.IntegerProperty()

  service_type = EnumProperty(datamodel.ServiceType)
  service_detail = ndb.StringProperty()

  times = ndb.LocalStructuredProperty(ServiceTime, repeated=True)
  not_dates = ndb.LocalStructuredProperty(ServiceNotDate, repeated=True)

  requires_ticket = ndb.BooleanProperty()
  requires_local_addr = ndb.BooleanProperty()
  requires_church_attend = ndb.BooleanProperty()
  sixty_plus = ndb.BooleanProperty()

  extra_notes = ndb.TextProperty()

  def get_times_by_day(self):
    key = lambda t: t.day
    return dict(
        (day, list(times)) for day, times
        in groupby(sorted(self.times, key=key), key))


class ServicePhone(ndb.Model):
  number = ndb.StringProperty()
  days = ndb.IntegerProperty(repeated=True)
  start = ndb.TimeProperty()
  end = ndb.TimeProperty()
  

class Location(ndb.Model):
  org_name = ndb.StringProperty()

  name = ndb.StringProperty()
  address = ndb.TextProperty()
  geo = ndb.GeoPtProperty()
  phone = ndb.LocalStructuredProperty(ServicePhone)
  websites = ndb.StringProperty(repeated=True)

  services = ndb.LocalStructuredProperty(Service, repeated=True)

  accessible = ndb.BooleanProperty()
  extra_notes = ndb.TextProperty()

  last_modified = ndb.DateTimeProperty(auto_now=True)

  def service(self, service_id):
    for service in self.services:
      if service.service_id == service_id:
        return service

  def service_index(self, service_id):
    for i, service in enumerate(self.services):
      if service.service_id == service_id:
        return i

  def add_service(self):
    service = Service()
    if self.services:
      service.service_id = max(s.service_id for s in self.services) + 1
    else:
      service.service_id = 1
    self.services.append(service)
    return service

