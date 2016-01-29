from base import BaseHandler

class ApplyHandler(BaseHandler):
  """Handler for applying to be an admin."""

  def get(self):
    self.write_template('apply.html')
  
  def post(self):
    profile = self.backend.get_user_profile()
    profile.wants_admin = True

    self.backend.save(profile)

    self.response.write('Success!')

