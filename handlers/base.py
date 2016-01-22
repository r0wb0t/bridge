from datetime import date, timedelta, tzinfo
import os
import urllib

import jinja2
import webapp2

from google.appengine.ext.ndb import Future

import config
from datamodel import ServiceType

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), '../templates')),
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


class BaseHandler(webapp2.RequestHandler):
  def __init__(self, request, response):
    super(BaseHandler, self).__init__(request, response)
    self.backend = config.BACKEND

  def write_template(self, template_name, params={}):
    finalparams = dict(
      request=self.request,
      tz=PST,
      utc=UTC,
    )
    for k,v in params.iteritems():
      if isinstance(v, Future):
        finalparams[k] = v.get_result()
      else:
        finalparams[k] = v
      
    self.response.write(
        JINJA_ENVIRONMENT.get_template(template_name).render(finalparams))


def admin_required(orig):
  def handler_method(self, *args):
    if self.backend.is_user_admin():
      orig(self, *args)
    else:
      if self.request.method == 'GET':
        uri = self.request.uri
      else:
        uri = '/'
      self.redirect(self.backend.create_login_url(uri))
      
  return handler_method

# currently everybody needs to be an admin
login_required = admin_required
