from google.appengine.ext import ndb


class KioskLocation(ndb.Model):
  name = ndb.StringProperty()
  address = ndb.TextProperty()
  location = ndb.GeoPtProperty()


class MealSpec(ndb.Model):
  start = ndb.TimeProperty()
  end = ndb.TimeProperty()
  days = ndb.IntegerProperty(repeated=True)
  menu = ndb.StringProperty(repeated=True)


class FoodSource(ndb.Model):
  name = ndb.StringProperty()
  address = ndb.TextProperty()
  location = ndb.GeoPtProperty()
  phones = ndb.IntegerProperty(repeated=True)
  website = ndb.StringProperty()

  breakfast = ndb.StructuredProperty(MealSpec)
  lunch = ndb.StructuredProperty(MealSpec)
  snack = ndb.StructuredProperty(MealSpec)
  dinner = ndb.StructuredProperty(MealSpec)

  accessible = ndb.BooleanProperty()
  requires_ticket = ndb.BooleanProperty()
  requires_local_addr = ndb.BooleanProperty()
  requires_church_attend = ndb.BooleanProperty()

  extra_notes = ndb.TextProperty()

	
