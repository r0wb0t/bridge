from datetime import date, timedelta, tzinfo
import os
import urllib

import jinja2
import webapp2

from google.appengine.api import users
from google.appengine.ext.ndb import Future

import config
import datamodel

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), '../templates')),
    extensions=['jinja2.ext.autoescape', 'jinja2.ext.i18n', 'jinja2.ext.do'],
    autoescape=True)
JINJA_ENVIRONMENT.install_null_translations()

def export_types(*types):
  for t in types:
    JINJA_ENVIRONMENT.globals[t.__name__] = t

export_types(
    date,
    datamodel.LogItem,
    datamodel.LogItemType,
    datamodel.SearchSection,
    datamodel.ServiceType)


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
      is_user_admin=self.backend.is_user_admin(),
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
      current_user = users.get_current_user()
      if current_user is None:
        if self.request.method == 'GET':
          uri = self.request.uri
        else:
          uri = '/'
        self.redirect(self.backend.create_login_url(uri))
      else:
        self.response.write(
            'Admin access required. Request it <a href="/apply">here</a>.')
      
  return handler_method

def login_required(orig):
  def handler_method(self, *args):
    current_user = users.get_current_user()
    if current_user is None:
      if self.request.method == 'GET':
        uri = self.request.uri
      else:
        uri = '/'
      self.redirect(self.backend.create_login_url(uri))
    else:
      orig(self, *args)
      
  return handler_method
