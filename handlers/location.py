from datetime import datetime, timedelta

from base import BaseHandler, login_required

from datamodel import Query, Field
import config

class LocationHandler(BaseHandler):
  @login_required
  def get(self, loc_id):
    query = Query()
    query.add_filter(Field.LOCATION_ID, int(loc_id))
    results = self.backend.search(query)

    self.write_template('details.html', {
      'origin': config.LOCATION_CRITERION.get_geo(self.request),
      'results': results,
      'now': datetime.now() - timedelta(hours=8),
    })
