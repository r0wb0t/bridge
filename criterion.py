import urllib
import urlparse


class Criterion(object):
  def __init__(self, slug, title, args, template):
    self.slug = slug
    self.title = title
    self.args = set(args)
    self.template = template

  def specified_by(self, request):
    return any(arg in request.arguments() for arg in self.args)

  def bind(self, request, service_path):
    return Option(self, request, service_path)


class Option(object):
  """An Option represents a value assigned to a Criterion """
  def __init__(self, criterion, request, service_path):
    self.criterion = criterion
    self.request = request
    self.service_path = service_path

  def add_to_query(self, query):
    return self.criterion.add_to_query(self.request, query)

  def annotate_entity(self, entity):
    self.criterion.annotate_entity(self.request, entity)

  def desc_value(self):
    return self.criterion.desc_value(self.request)

  def get_query_url(self):
    args = {}
    
    for name in self.request.arguments():
      args[name] = self.request.get(name)

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
    super(LocationCriterion, self).__init__(slug, title, ['geo'], 'location.html')
    self.geo_prop = geo_prop

  def add_to_query(self, request, query):
    return query

  def desc_value(self, request):
    return request.get('geo')
  

class YesNoCriterion(Criterion):
  def __init__(self, slug, title, yes_desc, no_desc, question, arg, bool_prop):
    super(YesNoCriterion, self).__init__(
        slug, title, ['%s_%s' % (arg, val) for val in ('yes','no')], 'yesno.html')
    self.arg = arg
    self.yes_arg = '%s_yes' % self.arg
    self.yes_desc = yes_desc
    self.no_desc = no_desc
    self.question = question
    self.bool_prop = bool_prop

  def add_to_query(self, request, query):
    if self.yes_arg in request.arguments():
      return query.filter(self.bool_prop == True)
    else:
      return query

  def annotate_entity(self, request, entity):
    if self.yes_arg in request.arguments():
      val = entity.to_dict()[self.bool_prop._name]
  
  def desc_value(self, request):
    if self.yes_arg in request.arguments():
      return self.yes_desc
    else:
      return self.no_desc

