from datetime import datetime, timedelta
from collections import namedtuple
from urlparse import urlparse, urlunparse
import itertools

from base import BaseHandler, login_required

import config
from datamodel import OhanaBackend, Query, SearchContext, ServiceType, LatLong


def handlers_for_service(criteria, slug):
  class QueryHandler(BaseHandler):
    @login_required
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
    @login_required
    def get(self):
      options = []
      context = SearchContext(datetime.now() - timedelta(hours=8))
      query = Query()

      for criterion in criteria:
        options.append(criterion.bind(self.request, '/services/%s' % slug));
        options[-1].add_to_query(query)

      results = itertools.groupby(
          self.backend.search(query, context),
          lambda result: result.section())

      Section = namedtuple('Section', ['section', 'results'])
      groups = []
      for result in results:
        groups.append(Section(result[0], list(result[1])))
      
      #for option in options:
      #  option.postprocess_results(results)

      self.write_template('list.html', {
        'origin': config.LOCATION_CRITERION.get_geo(self.request),
        'options': options,
        'results': groups,
        'search_context': context,
      })


  return [
    ('/services/%s' % slug, QueryHandler),
    ('/services/%s/all' % slug, ResultsHandler),
  ]
