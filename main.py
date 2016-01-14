from datetime import time, datetime, timedelta, tzinfo, date
import os
import re
from urlparse import urlparse, urlunparse
import urllib

import jinja2
import webapp2

from google.appengine.ext import ndb
from google.appengine.api import users

import config
from models import Location, Service, ServiceTime
from ohana import Ohana
from query import OhanaBackend, Query, ServiceType, LatLong
from backends import AppEngineBackend


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape', 'jinja2.ext.i18n'],
    autoescape=True)
JINJA_ENVIRONMENT.install_null_translations()

JINJA_ENVIRONMENT.globals['date'] = date
ServiceType.export_to(JINJA_ENVIRONMENT)

def urlencode_filter(s):
  return urllib.quote_plus(s)

JINJA_ENVIRONMENT.filters['urlencode'] = urlencode_filter

class FixedOffsetTimeZone(tzinfo):
  """Fixed offset in hours east from UTC."""

  def __init__(self, offset, name):
    self.__offset = timedelta(hours = offset)
    self.__name = name

  def utcoffset(self, dt):
    return self.__offset

  def tzname(self, dt):
    return self.__name

  def dst(self, dt):
    return timedelta(0)
      
UTC = FixedOffsetTimeZone(0, 'UTC')
PST = FixedOffsetTimeZone(-8, 'PST')

#USER_AGENT = 'Bridge/0.0.1' 
#OHANA = Ohana('http://api.smc-connect.org', USER_AGENT)
#BACKEND = OhanaBackend(OHANA)
BACKEND = AppEngineBackend()


class BaseHandler(webapp2.RequestHandler):
  def write_template(self, template_name, params={}):
    params.update(
      request=self.request,
      tz=PST,
      utc=UTC)
    self.response.write(
        JINJA_ENVIRONMENT.get_template(template_name).render(params))


class MainHandler(BaseHandler):
  def get(self):
    self.write_template('index.html')


class LogoutHandler(BaseHandler):
  def get(self):
    self.redirect(users.create_logout_url('/'))


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
    days = ['mon','tue','wed','thu','fri','sat','sun']
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
        days=[days.index(d) for d in days
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
      if self.request.get('service_id'):
        redirect_url = '%s&service_id=%s' % (
            redirect_url,
            self.request.get('service_id'))
    self.redirect(redirect_url)


def handlers_for(criteria, slug):
  class QueryHandler(BaseHandler):
    def get(self):
      next_criterion = None
      skip_all = False

      if 'q' in self.request.arguments():
        for criterion in criteria:
          if criterion.slug == self.request.get('q'):
            next_criterion = criterion
            skip_all = True
            break
        
      if not next_criterion:
        for criterion in criteria:
          if not criterion.specified_by(self.request):
            next_criterion = criterion
            break

      if not next_criterion:
        self.redirect(urlunparse((
            '',
            '',
            '/services/%s/all' % slug,
            '',
            self.request.query_string,
            '')))
        return

      other_args = {}
      for name, value in self.request.params.iteritems():
        if name != 'q' and name not in next_criterion.args:
          other_args[name] = value

      previous = None
      referrer = (self.request.referrer is not None
          and urlparse(self.request.referrer)
          or None)
      if referrer.netloc == self.request.host:
        previous = urlunparse(('', '', referrer.path, '', referrer.query, ''));

      self.write_template('query.html', {
        'criterion': next_criterion,
        'other_args': other_args,
        'skip_all': skip_all,
        'previous': previous,
      })


  class ResultsHandler(BaseHandler):
    def get(self):
      options = []
      query = Query()

      for criterion in criteria:
        options.append(criterion.bind(self.request, '/services/%s' % slug));
        options[-1].add_to_query(query)

      results = BACKEND.search(query)

      for option in options:
        option.postprocess_results(results)

      self.write_template('list.html', {
        'origin': config.LOCATION_CRITERION.get_geo(self.request),
        'options': options,
        'results': results,
        'now': datetime.now(),
      })


  return [
    ('/services/%s' % slug, QueryHandler),
    ('/services/%s/all' % slug, ResultsHandler),
  ]


app = webapp2.WSGIApplication(
  [('/', MainHandler),
   ('/logout', LogoutHandler),
   ('/edit', EditHandler)] +
      handlers_for(config.FOOD_CRITERIA, 'food'),
  debug=True)
