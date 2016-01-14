import urllib
import urlparse

from geo_utils import by_closeness_to
from query import LatLong

# Criterion.
#
# Criteria translate between the HTTP request params and the query.

class Criterion(object):
  """A Criterion is a part of the query that must be fulfilled to get results.
  """
  def __init__(self, slug, title, args, template, has_default=False):
    self.slug = slug
    self.title = title
    self.args = set(args)
    self.template = template
    self.has_default = has_default

  def specified_by(self, request):
    """Returns true if this criterion is fulfilled by the request."""
    return (self.has_default or
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
  def __init__(self,
               slug,
               title,
               geo_field,
               default_name=None,
               default_geo=None):
    super(LocationCriterion, self).__init__(
        slug,
        title,
        ['geo', 'geo_name'],
        'location.html',
        has_default=(default_geo is not None))
    self.geo_field = geo_field
    self.default_name = default_name
    self.default_geo = default_geo

  def get_name(self, request):
    if 'geo_name' in request.params:
      return request.get('geo_name')
    else:
      return self.default_name

  def get_geo(self, request):
    if 'geo_name' in request.params:
      return  LatLong.from_str(request.get('geo'))
    else:
      return self.default_geo

  def desc_value(self, request):
    name = self.get_name(request)
    if name is not None:
      return 'Near %s' % name
    geo = self.get_geo(request)
    if geo is not None:
      return 'Near %s, %s' % (geo.lat, geo.lon)
    return 'Unknown'

  def add_to_query(self, request, query):
    geo = self.get_geo(request)
    if geo is not None:
      query.add_filter(self.geo_field, geo)

  def postprocess_results(self, request, results):
    geo = self.get_geo(request)
    if geo is not None:
      pass
      #results.sort(
      #    by_closeness_to(geo),
      #    key=lambda r: r.location)


class YesNoCriterion(Criterion):
  def __init__(self,
               slug,
               title,
               yes_desc,
               no_desc,
               question,
               bool_field,
               default = None,):
    super(YesNoCriterion, self).__init__(
        slug = slug,
        title = title,
        args = ['%s_%s' % (slug, val) for val in ('yes','no')],
        template = 'yesno.html',
        has_default = (default is not None))
    self.yes_arg = '%s_yes' % self.slug
    self.no_arg = '%s_no' % self.slug
    self.yes_desc = yes_desc
    self.no_desc = no_desc
    self.question = question
    self.bool_field = bool_field
    self.default = default

  def get_value(self, request):
    if self.yes_arg in request.params:
      return True
    if self.no_arg in request.params:
      return False
    else:
      return self.default

  def add_to_query(self, request, query):
    value = self.get_value(request)
    if value is not None:
      query.add_filter(self.bool_field, value)

  def annotate_result(self, request, result):
    if self.yes_arg in request.params:
      pass
      # val = result.to_dict()[self.bool_prop._name]
      # TODO(rnairn): Add annotation.
  
  def desc_value(self, request):
    value = self.get_value(request)
    if value is None:
      return 'Any'
    else:
      return [self.no_desc, self.yes_desc][value]
