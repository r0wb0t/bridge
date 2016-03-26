from datetime import datetime, timedelta
import itertools
from collections import defaultdict

from google.appengine.api import users
from google.appengine.ext import ndb

from appengine import models
import datamodel
from datamodel import Field, LatLong, Ranker, SearchResult
from backendbase import BackendBase


class AppEngineBackend(BackendBase):
  def __init__(self):
    self.admins = set()
    self.typedict = {
      datamodel.UserProfile: models.UserProfile,
      datamodel.AdminInvite: models.AdminInvite,
    }

  def is_user_admin(self):
    if users.is_current_user_admin():
      return True

    current_user = users.get_current_user()
    if current_user is None:
      return False
    
    if current_user.user_id() in self.admins:
      return True

    profile = models.UserProfile.for_user_id(current_user.user_id())
    if profile.message.is_admin:
      self.admins.add(current_user.user_id())
      return True
    return False

  def create_login_url(self, redirect):
    return users.create_login_url(redirect)

  def create_logout_url(self, redirect):
    return users.create_logout_url(redirect)

  def get_user_profile(self, user_id=None):
    email = None
    if user_id is None:
      assert users.get_current_user() 
      user_id = users.get_current_user().user_id()
      email = users.get_current_user().email()
    profile = models.UserProfile.for_user_id(user_id).message
    if email and not profile.email:
      profile.email = email
    return profile

  def get_by_id(self, datatype, id):
    return self.typedict[datatype].get_by_id(id).message

  def save(self, dataobject):
    self.typedict[type(dataobject)](message=dataobject).put()    

  def delete_async(self, dataobject):
    model_type = self.typedict[type(dataobject)]
    id = model_type(message=dataobject).get_id()
    return ndb.Key(model_type, id).delete_async()    

  @ndb.tasklet
  def find(self, datatype, **kwargs):
    queryargs = []
    modeltype = self.typedict[datatype]
    for k,v in kwargs.iteritems():
      prop = modeltype.message.__getattr__(k)
      queryargs.append(prop == v)

    results = yield self.typedict[datatype].query(*queryargs).fetch_async()
    for result in results:
      result.populate_id()
    raise ndb.Return(result.message for result in results);

  def search(self, query, context):
    if query.get(Field.LOCATION_ID) is not None:
      location = models.Location.get_by_id(query.get(Field.LOCATION_ID))
      assert location
      locations = [location]
    else:
      locations = models.Location.query()
      if query.get(Field.ACCESSIBLE) is not None:
        locations.filter(models.Location.accessible == query.get(Field.ACCESSIBLE))

    results = itertools.chain(*(
        self.make_results(loc, query, context) for loc in locations))
    return Ranker(query).rerank(results)  

  def make_results(self, loc, query, context):
    results = []
    for service in loc.services:
      if self.matches_service(query, service):
        result = SearchResult(
            context,
            name=loc.name,
            address=loc.address,
            location=LatLong.from_geo(loc.geo),
            website=loc.websites and loc.websites[0] or None)
        result.id = loc.key.id()
        result.phone = loc.phone
        result.accessible = loc.accessible
        result.service_id = service.service_id
        result.service_type = service.service_type
        result.service_detail = service.service_detail
        result.service_times = service.times
        result.service_days = defaultdict(list)
        for time in result.service_times:
          if time.start:
            result.service_days[time.day].append(time)
        for times in result.service_days.viewvalues():
          times.sort(key=lambda time: time.start)

        result.service_notes = service.extra_notes
        result.last_modified = loc.last_modified
        results.append(result)
    return results

  def matches_service(self, query, service):
    return True

  def matches_service_time(self, query, service_time):
    return True


