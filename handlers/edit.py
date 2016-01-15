from datetime import datetime
import re

from google.appengine.ext import ndb

from appengine.models import Location, Service, ServiceTime
from handlers.base import BaseHandler


class EditHandler(BaseHandler):
  def get(self):
    loc = None
    service = None
    if self.request.get('id'):
      loc = Location.get_by_id(int(self.request.get('id')))

      if self.request.get('service_id'):
        service = loc.service(int(self.request.get('service_id')))

    all_locs = Location.query().order(Location.name)

    self.write_template('form.html', {
      'all_locs': all_locs,
      'loc': loc,
      'service': service,
      'redirect_to': self.request.get('r'),
    })

  @ndb.transactional
  def post(self):
    day_names = ['mon','tue','wed','thu','fri','sat','sun']
    item = None
    if self.request.get('id'):
      loc = Location.get_by_id(int(self.request.get('id')))
    else:
      loc = Location()
    loc.populate(
        name=self.request.get('name'),
        address=self.request.get('address'),
        geo=LatLong.to_geo(LatLong.from_str(self.request.get('location'))),
        phones=[int(re.sub(r'[^0-9]+', '', p))
                for p in self.request.get('phones').splitlines()
                if len(p.strip()) > 0],
        websites=[self.request.get('website')],
        accessible='accessible' in self.request.arguments())
    
    service = None
    service_type = self.request.get('service_type')
    service_detail = self.request.get('service_detail')

    if service_type or service_detail:
      service = None
      if self.request.get('service_id'):
        service = loc.service(int(self.request.get('service_id')))
      if service is None:
        service = loc.add_service()

      service.populate(
          service_type=(service_type
              and ServiceType.for_name(service_type)
              or None),
          service_detail=service_detail,
          requires_ticket='requires_ticket' in self.request.arguments(),
          requires_local_addr='requires_local_addr' in self.request.arguments(),
          requires_church_attend=(
              'requires_church_attend' in self.request.arguments()),
          extra_notes=self.request.get('service_notes'))

      service.times = []
      num_times = min(100, int(self.request.get('num_times')))
      for i in range(num_times):
        time_arg = lambda name: '%s_%s' % (name, i)
        days=[day_names.index(d) for d in day_names
              if time_arg('days_%s' % d) in self.request.arguments()]
        if days:
          parse_time = lambda s: datetime.strptime(s, '%H:%M').time()
          service.times.append(ServiceTime(
              start=parse_time(self.request.get(time_arg('start'))),
              end=parse_time(self.request.get(time_arg('end'))),
              days=days))

      service.not_dates = []
      num_not_dates = min(100, int(self.request.get('num_not_dates')))
      for i in range(num_times):
        arg = lambda name: 'not_date_%s_%s' % (i, name)
        if self.request.get(arg('month')):
          service.not_dates.append(date(
              2000,
              int(self.request.get(arg('month'))),
              int(self.request.get(arg('day')))));
   
    loc.put()
    redirect_url = self.request.get('r')
    if not redirect_url:
      redirect_url = '/edit?id=%s' % loc.key.id()
      if service:
        redirect_url = '%s&service_id=%s' % (
            redirect_url,
            service.service_id)
        
    self.redirect(redirect_url)
