from abc import ABCMeta, abstractmethod

class BackendBase(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def is_user_admin(self):
    pass

  @abstractmethod
  def create_login_url(self, redirect):
    pass

  @abstractmethod
  def create_logout_url(self, redirect):
    pass

  @abstractmethod
  def search(self, query):
    pass


    
