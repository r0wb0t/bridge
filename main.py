from datetime import time
import os
import urlparse

import jinja2
import webapp2

from google.appengine.ext import ndb

import config
from criterion import LocationCriterion, Query
from models import KioskLocation, FoodSource, MealSpec
from ohana import Ohana


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


DEFAULT_KIOSK = KioskLocation(
    name='Project Homeless Connect',
    address='25 Van Ness Ave',
    location=ndb.GeoPt(37.774929, -122.419416))


USER_AGENT = 'Bridge/0.0.1' 
OHANA = Ohana('http://api.smc-connect.org', USER_AGENT)


class Backend:
  OHANA = 'ohana'
  APPENGINE = 'appengine'


BACKEND = Backend.OHANA


class MainHandler(webapp2.RequestHandler):
  def get(self):
    self.response.write(JINJA_ENVIRONMENT.get_template('index.html').render({
      'location': DEFAULT_KIOSK,
    }))


class PopulateHandler(webapp2.RequestHandler):
  def get(self):
    self.response.write(JINJA_ENVIRONMENT.get_template('form.html').render())

  def post(self):
    days = ['mon','tue','wed','thu','fri','sat','sun']
    source = FoodSource(
        name=self.request.get('name'),
        address=self.request.get('address'),
        location=ndb.GeoPt(
            self.request.get('location').split(',')[0],
            self.request.get('location').split(',')[1]),
        phones=[int(re.sub(r'[^0-9]+', '', p))
                for p in self.request.get('phones').splitlines()
                if len(p.strip()) == 0],
        website=self.request.get('website'),
        breakfast=MealSpec(
            start=time(int(self.request.get('breakfast_start'))),
            end=time(int(self.request.get('breakfast_end'))),
            days=[days.index(d) for d in days
                  if 'breakfast_days_%s' % d in self.request.arguments()],
            menu=self.request.get('breakfast_menu').splitlines()),
        lunch=MealSpec(
            start=time(int(self.request.get('lunch_start'))),
            end=time(int(self.request.get('lunch_end'))),
            days=[days.index(d) for d in days
                  if 'lunch_days_%s' % d in self.request.arguments()],
            menu=self.request.get('lunch_menu').splitlines()),
        snack=MealSpec(
            start=time(int(self.request.get('snack_start'))),
            end=time(int(self.request.get('snack_end'))),
            days=[days.index(d) for d in days
                  if 'snack_days_%s' % d in self.request.arguments()],
            menu=self.request.get('snack_menu').splitlines()),
        dinner=MealSpec(
            start=time(int(self.request.get('dinner_start'))),
            end=time(int(self.request.get('dinner_end'))),
            days=[days.index(d) for d in days
                  if 'dinner_days_%s' % d in self.request.arguments()],
            menu=self.request.get('dinner_menu').splitlines()),
        accessible='accessible' in self.request.arguments(),
        requires_ticket='requires_ticket' in self.request.arguments(),
        requires_local_addr='requires_local_addr' in self.request.arguments(),
        requires_church_attend=(
            'requires_church_attend' in self.request.arguments()),
        extra_notes=self.request.get('extra_notes'))
    source.put()
    self.redirect('/populate')


def handlers_for(criteria, model, slug):
  class QueryHandler(webapp2.RequestHandler):
    def get(self):
      LocationCriterion.maybe_add_defaults(DEFAULT_KIOSK, self.request)
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
        self.redirect(urlparse.urlunparse((
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

      self.response.write(JINJA_ENVIRONMENT.get_template('query.html').render({
        'kiosk': DEFAULT_KIOSK,
        'criterion': next_criterion,
        'other_args': other_args,
        'skip_all': skip_all,
      }))


  class ResultsHandler(webapp2.RequestHandler):
    def get(self):
      LocationCriterion.maybe_add_defaults(DEFAULT_KIOSK, self.request)
      options = []
      query = Query()

      for criterion in criteria:
        options.append(criterion.bind(self.request, '/services/%s' % slug));
        options[-1].add_to_query(query)

      if BACKEND == Backend.OHANA:
        results = query.exec_ohana(OHANA)
      elif BACKEND == Backend.APPENGINE:
        results = query.exec_appengine()

      for option in options:
        option.postprocess_results(results)

      self.response.write(JINJA_ENVIRONMENT.get_template('list.html').render({
        'kiosk': DEFAULT_KIOSK,
        'origin': LocationCriterion.get_geo_pt(self.request),
        'options': options,
        'results': results
      }))


  return [
    ('/services/%s' % slug, QueryHandler),
    ('/services/%s/all' % slug, ResultsHandler),
  ]


app = webapp2.WSGIApplication(
  [('/', MainHandler),
   ('/populate', PopulateHandler)] +
      handlers_for(config.FOOD_CRITERIA, FoodSource, 'food'),
  debug=True)
