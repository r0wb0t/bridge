# Wrapper for http://codeforamerica.github.io/ohana-api-docs

import json
from urllib import urlencode
from urllib2 import urlopen, Request

ACCEPT_HEADER = 'application/vnd.ohanapi+json; version=1'
REQUEST_TIMEOUT_SEC = 10.0

class Ohana:
  class Category:
    FOOD = 'Food'

  def __init__(self, root, user_agent):
    self.root = root
    self.user_agent = user_agent

  def search(self,
             categories=[],
             keywords=None,
             latitude=None,
             longitude=None,
             status='active'):
    params = (
      [('status', status),] +
      [('category[]', category) for category in categories])
    if keywords is not None:
      params.append(('keyword', keywords))
    if latitude is not None:
      assert longitude is not None
      params.append(('lat_lng', '%s,%s' % (latitude, longitude)))

    endpoint = '%s/search?%s' % (self.root, urlencode(params))

    req = Request(endpoint,
                  headers={
                     'User-Agent': self.user_agent,
                     'Accept': ACCEPT_HEADER})
    resp = urlopen(req, timeout=REQUEST_TIMEOUT_SEC)
    assert resp.getcode() == 200
    return [Location(**result) for result in json.load(resp)]


class Location:
  def __init__(self,
               id,
               name=None,
               address=None,
               website=None,
               latitude=None,
               longitude=None,
               **kwargs):
    self.id = id
    self.name = name
    self.address = address is None and Address(**address) or None
    self.website = website
    self.latitude = latitude
    self.longitude = longitude

    self.other_properties = kwargs


class Address:
  def __init__(self,
               address_1=None,
               city=None,
               state_province=None,
               postal_code=None,
               address_2=None,
               **kwargs):
    self.address_1 = address_1
    self.address_2 = address_2
    self.city = city
    self.state_province = state_province
    self.postal_code = postal_code
    self.other_properties = kwargs

  def __str__(self):
    lines = [
      self.address_1,
      self.address_2,
      self.city,
      '%s %s' % (self.state_province, self.postal_code),]
    return ',\n'.join([line for line in lines if line is not None])
    
