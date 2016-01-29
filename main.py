from urlparse import urlparse, urlunparse

import webapp2

from google.appengine.api import users

import config
from handlers import *

class LogoutHandler(webapp2.RequestHandler):
  def get(self):
    self.redirect(users.create_logout_url('/'))


app = webapp2.WSGIApplication(
  [('/', IndexHandler),
   ('/apply', ApplyHandler),
   ('/logout', LogoutHandler),
   ('/makeadmin', MakeAdminHandler),
   ('/edit', EditHandler),
   ('/locations/(.*)', LocationHandler)] +
      handlers_for_service(config.FOOD_CRITERIA, 'food'),
  debug=True)
