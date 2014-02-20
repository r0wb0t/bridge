import math

def distance(pt1, pt2):
  x = (pt2.lon - pt1.lon) * math.cos((pt1.lat + pt2.lat) / 2);
  y = (pt2.lat - pt1.lat);
  return math.sqrt(x * x + y * y)

def by_closeness_to(pt):
  """Given a ndb.GeoPt <pt> returns a comparison function suitable for use in
     list.sort which compares by increasing distance to <pt>.
  """
  def closer(a, b):
    return round_towards_inf(distance(a, pt) - distance(b, pt))

  return closer

def round_towards_inf(x):
  return int(math.copysign(math.ceil(abs(x)), x))
