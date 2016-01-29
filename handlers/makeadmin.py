from base import BaseHandler, admin_required

from datamodel import UserProfile

class MakeAdminHandler(BaseHandler):
  """Handler for applying to be an admin."""

  @admin_required
  def get(self):
    self.write_template('makeadmin.html', {
      'is_admin': self.backend.find(UserProfile, is_admin=True),
      'wants_admin': (
          self.backend.find(UserProfile, wants_admin=True, is_admin=False))
    })
  
  @admin_required
  def post(self):
    profile = self.backend.get_by_id(UserProfile, self.request.get('id'))
    assert profile
    profile.is_admin = True
    profile.wants_admin = None

    self.backend.save(profile)

    self.redirect('/makeadmin')

