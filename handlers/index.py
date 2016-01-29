from handlers.base import BaseHandler


class IndexHandler(BaseHandler):
  def get(self):
    self.write_template('index.html')

