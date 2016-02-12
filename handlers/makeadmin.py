import base64
import os

from base import BaseHandler, admin_required

from datamodel import AdminInvite, UserProfile

class MakeAdminHandler(BaseHandler):
  """Handler for applying to be an admin."""

  def get(self):
    if self.request.get('code'):
      invites = list(
          self.backend.find(AdminInvite, code=self.request.get('code'))
              .get_result())
      if invites:
        profile = self.backend.get_user_profile()
        profile.is_admin = True
        self.backend.save(profile)
        self.backend.delete_async(invites[0]).wait()
        self.redirect('/admin')
      else:
        self.response.write('Code invalid')
    else:
      self.show_admin_page()

  @admin_required
  def show_admin_page(self):
    self.write_template('makeadmin.html', {
      'is_admin': self.backend.find(UserProfile, is_admin=True),
      'wants_admin': (
          self.backend.find(UserProfile, wants_admin=True, is_admin=False))
    })
  
  @admin_required
  def post(self):
    if self.request.get('id'):
      profile = self.backend.get_by_id(UserProfile, self.request.get('id'))
      assert profile
      profile.is_admin = True
      profile.wants_admin = None

      self.backend.save(profile)

      self.redirect('/admin')
    else:
      code = base64.urlsafe_b64encode(os.urandom(16))
      invite = AdminInvite(code=code)
      self.backend.save(invite)
      self.response.write(
          '%s/admin?code=%s' % (self.request.host_url, code))
