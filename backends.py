import itertools

from models import Location
from query import Field, LatLong, SearchResult
    

class AppEngineBackend:
  def search(self, query):
    q = Location.query()

    if query.get(Field.ACCESSIBLE) is not None:
      q.filter(Location.accessible == query.get(Field.ACCESSIBLE))

    results = itertools.chain(*(self.make_results(loc, query) for loc in q))
    return self.rerank(results, query)  

  def make_results(self, loc, query):
    results = []
    for service in loc.services:
      if self.matches_service(query, service):
        result = SearchResult(
            name=loc.name,
            address=loc.address,
            location=LatLong.from_geo(loc.geo),
            website=loc.websites and loc.websites[0] or None)
        result.id = loc.key.id()
        result.service_id = service.service_id
        result.service_type = service.service_type
        result.service_detail = service.service_detail
        result.service_times = service.times
        results.append(result)
    return results

  def matches_service(self, query, service):
    return True

  def matches_service_time(self, query, service_time):
    return True

  def rerank(self, results, query):
    return list(results)
