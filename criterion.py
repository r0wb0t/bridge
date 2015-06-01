import urllib
import urlparse

from geo_utils import by_closeness_to
from ohana import Ohana

class LatLong:
  def __init__(self, lat, lon):
    self.lat = lat
    self.lon = lon

  @classmethod
  def from_str(cls, s):
    return LatLong(*[float(d) for d in s.split(',')])


class SearchResult:
  def __init__(self, name, address, location=None, phones=[], website=None):
    self.name = name
    self.address = address
    self.location = location
    self.phones = phones
    self.website = website

  @classmethod
  def from_ohana_location(cls, loc):
    return SearchResult(name=loc.name,
                        address=str(loc.address),
                        location=LatLong(loc.latitude, loc.longitude),
                        website=loc.website)


class Query:
  def __init__(self):
    self.location = None

  def add_location(self, loc):
    self.location = loc

  def add_filter(self, prop, value):
    # TODO(rnairn): Save filters.
    pass

  def exec_ohana(self, ohana):
    params = {'keywords': 'food'}
    if self.location is not None:
      params['latitude'] = self.location.lat
      params['longitude'] = self.location.lon

    return [SearchResult.from_ohana_location(loc)
            for loc in ohana.search(**params)]

  def exec_appengine(self):
    q = FoodSource.query()
    # TODO(rnairn): Add filters etc.
    return list(q)


class Criterion(object):
  """A Criterion is a part of the query that must be fulfilled to get results.
  """
  def __init__(self, slug, title, args, template, default=None):
    self.slug = slug
    self.title = title
    self.args = set(args)
    self.template = template
    self.default = default

  def specified_by(self, request):
    """Returns true if this criterion is fulfilled by the request."""
    return (self.default is not None or
        any(arg in request.params for arg in self.args))

  def bind(self, request, service_path):
    return Option(self, request, service_path)

  def add_to_query(self, request, query):
    pass

  def postprocess_results(self, request, results):
    pass

  def annotate_result(self, request, entity):
    pass


class Option(object):
  """An Option represents a value assigned to a Criterion """
  def __init__(self, criterion, request, service_path):
    self.criterion = criterion
    self.request = request
    self.service_path = service_path

  def add_to_query(self, query):
    self.criterion.add_to_query(self.request, query)

  def postprocess_results(self, results):
    self.criterion.postprocess_results(self.request, results)
    for result in results:
      self.criterion.annotate_result(self.request, result)

  def desc_value(self):
    return self.criterion.desc_value(self.request)

  def get_query_url(self):
    args = dict(self.request.params)
    args['q'] = self.criterion.slug
    
    return urlparse.urlunparse((
        '',
        '',
        self.service_path,
        '',
        urllib.urlencode(args),
        ''))


class LocationCriterion(Criterion):
  def __init__(self, slug, title, geo_prop):
    super(LocationCriterion, self).__init__(
        slug, title, ['geo', 'geo_name'], 'location.html')
    self.geo_prop = geo_prop

  def desc_value(self, request):
    return 'Near %s' % (request.get('geo_name') or request.get('geo'))

  def add_to_query(self, request, query):
    query.add_location(LocationCriterion.get_geo_pt(request))

  def postprocess_results(self, request, results):
    if 'geo' in request.params:
      pt = LatLong.from_str(request.params['geo'])
      results.sort(
          by_closeness_to(pt),
          key=lambda r: r.location)

  @staticmethod
  def maybe_add_defaults(kiosk_loc, request):
    """Add fake geo properties to the request if they are not specified
       manually.
    """
    if 'geo' not in request.params:
      request.GET['geo'] = str(kiosk_loc.location)
      request.GET['geo_name'] = kiosk_loc.name

  @staticmethod
  def get_geo_pt(request):
    if 'geo' in request.params:
      return LatLong.from_str(request.params['geo'])
    return None


class YesNoCriterion(Criterion):
  def __init__(self,
               slug,
               title,
               yes_desc,
               no_desc,
               question,
               bool_prop,
               default = None,
               dominant = True):
    super(YesNoCriterion, self).__init__(
        slug = slug,
        title = title,
        args = ['%s_%s' % (slug, val) for val in ('yes','no')],
        template = 'yesno.html',
        default = default)
    self.yes_arg = '%s_yes' % self.slug
    self.no_arg = '%s_no' % self.slug
    self.yes_desc = yes_desc
    self.no_desc = no_desc
    self.question = question
    self.bool_prop = bool_prop
    self.dominant = dominant

  def add_to_query(self, request, query):
    if [self.no_arg, self.yes_arg][self.dominant] in request.params:
      query.add_filter(self.bool_prop, self.dominant)

  def annotate_result(self, request, result):
    if self.yes_arg in request.params:
      pass
      # val = result.to_dict()[self.bool_prop._name]
      # TODO(rnairn): Add annotation.
  
  def desc_value(self, request):
    if self.yes_arg in request.params:
      return self.yes_desc
    elif self.default is None:
      return self.no_desc
    else:
      return [self.no_desc, self.yes_desc][self.default]

