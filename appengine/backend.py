from datetime import datetime, timedelta
import itertools
from collections import defaultdict

from appengine.models import Location
from datamodel import Field, LatLong, SearchResult
from backendbase import BackendBase


class AppEngineBackend(BackendBase):
  def search(self, query):
    q = Location.query()

    if query.get(Field.ACCESSIBLE) is not None:
      q.filter(Location.accessible == query.get(Field.ACCESSIBLE))

    results = itertools.chain(*(self.make_results(loc, query) for loc in q))
    return Ranker(query).rerank(results)  

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
        result.phones = loc.phones
        result.accessible = loc.accessible
        result.service_id = service.service_id
        result.service_type = service.service_type
        result.service_detail = service.service_detail
        result.service_times = service.times
        result.service_days = defaultdict(list)
        for time in result.service_times:
          for day in time.days:
            result.service_days[day].append(time)
        for times in result.service_days.viewvalues():
          times.sort(key=lambda time: time.start)

        result.service_notes = service.extra_notes
        result.last_modified = loc.last_modified
        results.append(result)
    return results

  def matches_service(self, query, service):
    return True

  def matches_service_time(self, query, service_time):
    return True


class Ranker(object):
  def __init__(self, query):
    self.query = query
    self.now = datetime.now() - timedelta(hours=8)

  def rerank(self, results):
    results = list(results)
    results.sort(key=self.score)
    return results

  def score(self, result):
    return self.dayscore(result)

  def dayscore(self, result):
    days = set()
    for service_time in result.service_times:
      for day in service_time.days:
        days.add(day)
    if len(days) == 0:
      return 10
    return min((day - self.now.weekday()) % 7 for day in days)
