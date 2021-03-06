from google.appengine.ext import ndb

from appengine.backend import AppEngineBackend
from criterion import Criterion, LocationCriterion, YesNoCriterion 
from appengine.models import KioskLocation, Location
from datamodel import Field


#USER_AGENT = 'Bridge/0.0.1' 
#OHANA = Ohana('http://api.smc-connect.org', USER_AGENT)
#BACKEND = OhanaBackend(OHANA)
BACKEND = AppEngineBackend()

DEFAULT_KIOSK = KioskLocation(
    name='Project Homeless Connect',
    address='25 Van Ness Ave',
    location=ndb.GeoPt(37.774929, -122.419416))

LOCATION_CRITERION = LocationCriterion(
    slug = 'loc',
    title = 'Location',
    geo_field = Field.LOCATION,
    default_name = DEFAULT_KIOSK.name,
    default_geo = DEFAULT_KIOSK.location)

FOOD_CRITERIA = [
  LOCATION_CRITERION,
  YesNoCriterion(
      slug = 'acc',
      title = 'Access',
      yes_desc = 'Wheelchair',
      no_desc = 'Any',
      question = 'Do you need wheelchair access?',
      bool_field = Field.ACCESSIBLE,
      default = False),
  YesNoCriterion(
      slug = 'age',
      title = 'Age',
      yes_desc = '60+',
      no_desc = 'Under 60',
      question = 'Are you 60 or older?',
      bool_field = Field.SIXTY_PLUS),
]
