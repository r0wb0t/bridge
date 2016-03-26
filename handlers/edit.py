from datetime import datetime, date
import re

from google.appengine.ext import ndb
from webob.multidict import MultiDict

from base import BaseHandler, login_required

from appengine import models
from appengine.models import Location, Service
from datamodel import LatLong, ServiceType


DAY_NAMES = ['mon','tue','wed','thu','fri','sat','sun']


class EditHandler(BaseHandler):
  @login_required
  def get(self):
    loc = None
    service_index = None
    if self.request.get('id'):
      loc = Location.get_by_id(int(self.request.get('id')))

      if self.request.get('service_id'):
        service_index = loc.service_index(int(self.request.get('service_id')))

    all_locs = Location.query().order(Location.name)

    self.write_template('form.html', {
      'all_locs': all_locs,
      'loc': loc,
      'service_index': service_index,
      'redirect_to': self.request.get('r'),
    })

  @login_required
  def post(self):
    if 'save' in self.request.params:
      if self.request.get('id'):
        loc, service = self.update(int(self.request.get('id')))
      else:
        loc, service = self.create()

      redirect_url = self.request.get('r')
      if not redirect_url:
        redirect_url = '/edit?id=%s' % loc.key.id()
        if service:
          redirect_url = '%s&service_id=%s' % (
              redirect_url,
              service.service_id)
        
      self.redirect(redirect_url)
    else:
      all_locs = Location.query().order(Location.name)

      if self.request.get('id'):
        loc = Location.get_by_id(int(self.request.get('id')))
      else:
        loc = Location()
      service = self.populate(loc)

      service_index = None
      if service:
        for i, s in enumerate(loc.services):
          if s is service:
            service_index = i

      removed_services = [int(s)
          for s in self.request.get('removed_services').split()]

      if 'add_service' in self.request.params:
        service = Service()
        loc.services.append(service)
        service_index = len(loc.services) - 1
      if 'remove_service' in self.request.params:
        assert service
        removed_services.append(service_index)
      if 'restore_service' in self.request.params:
        assert service
        removed_services.remove(service_index)
      elif 'add_time' in self.request.params:
        assert service
        day = DAY_NAMES.index(self.request.get('add_time'))
        assert 0 <= day < 7, day
        service.times.append(models.ServiceTime(day=day))
      elif 'remove_time' in self.request.params:
        assert service
        index = int(self.request.get('remove_time'))
        del service.times[index]
      elif 'add_not_date' in self.request.params:
        assert service
        service.not_dates.append(models.ServiceNotDate())
      elif 'remove_not_date' in self.request.params:
        assert service
        index = int(self.request.get('remove_not_date'))
        del service.not_dates[index]
      elif 'add_phone' in self.request.params:
        loc.phone = models.ServicePhone()
      elif 'remove_phone' in self.request.params:
        loc.phone = None

      self.write_template('form.html', {
        'all_locs': all_locs,
        'loc': loc,
        'service_index': service_index,
        'removed_services': removed_services,
        'redirect_to': self.request.get('r'),
      })

  def create(self):
    loc = Location()
    service = self.populate(loc, for_put=True)
    loc.put()
    return loc, service

  @ndb.transactional
  def update(self, loc_id):
    loc = Location.get_by_id(loc_id)
    service = self.populate(loc, for_put=True)
    loc.put()
    return loc, service

  def populate(self, loc, for_put=False):

    loc.populate(
        name=self.request.get('name'),
        address=self.request.get('address'),
        geo=LatLong.to_geo(LatLong.from_str(self.request.get('location'))),
        websites=[self.request.get('website')],
        accessible='accessible' in self.request.arguments())

    if 'phone_number' in self.request.params:
      subset = param_subset(self.request.params, 'phone_', '_0')
      start, end = parse_time_range(subset)

      loc.phone = models.ServicePhone(
          number=self.request.get('phone_number'),
          days=[d for d in range(7)
              if 'phone_day_%s' % d in self.request.params],
          start=start,
          end=end)
    
    service_index = None
    selected_service = None
    if 'switch_service' in self.request.params:
      service_index = int(self.request.get('switch_service'))
    elif 'service_index' in self.request.params:
      service_index = int(self.request.get('service_index'))
    
    num_services = min(100, int(self.request.get('num_services')))
    removed_services = [int(s)
        for s in self.request.get('removed_services').split()]

    for sindex in range(num_services):
      service_subset = param_subset(self.request.params, 's_%s_' % sindex)

      service = None
      if service_subset.get('service_id'):
        service = loc.service(int(service_subset.get('service_id')))
      if service is None:
        if for_put:
          service = loc.add_service()
        else:
          service = Service()
          loc.services.append(service)
      if for_put and sindex in removed_services:
        loc.services.remove(service)
        continue

      if service_index == sindex:
        selected_service = service

      service_type = service_subset.get('service_type')

      service.populate(
          service_type=(service_type
              and ServiceType.for_name(service_type)
              or None),
          service_detail=service_subset.get('service_detail'),
          requires_ticket='requires_ticket' in service_subset,
          requires_local_addr='requires_local_addr' in service_subset,
          requires_church_attend='requires_church_attend' in service_subset,
          extra_notes=service_subset.get('extra_notes'))

      service.times = []
      num_times = min(100, int(service_subset.get('num_times')))
      for i in range(num_times):
        subset = param_subset(service_subset, suffix='_%s' % i)
        if 'day' in subset:
          start, end = parse_time_range(subset)
          service.times.append(models.ServiceTime(
              day=DAY_NAMES.index(subset.get('day')),
              start=start,
              end=end))

      service.not_dates = []
      num_not_dates = min(100, int(service_subset.get('num_not_dates')))
      for i in range(num_not_dates):
        subset = param_subset(service_subset, 'not_date_%s_' % i)
        not_date = models.ServiceNotDate()
        service.not_dates.append(not_date)
        if subset.get('month'):
          not_date.month = int(subset.get('month'))
        if subset.get('day'):
          not_date.day = int(subset.get('day'))

    return selected_service
   

def param_subset(params, prefix='', suffix=''):
  return MultiDict([(k[len(prefix):(-len(suffix) or None)], v)
                    for k, v in params.iteritems()
                    if k.startswith(prefix) and k.endswith(suffix)])

def parse_time_range(params):
  parse_time = lambda h, m: datetime.strptime(h+m, '%H%M').time()
  return (parse_time(params.get('start_hr'), params.get('start_min')),
      parse_time(params.get('end_hr'), params.get('end_min')))
