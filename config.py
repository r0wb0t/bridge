
from criterion import Criterion, LocationCriterion, YesNoCriterion 
from models import FoodSource


FOOD_CRITERIA = [
  LocationCriterion('loc', 'Location', FoodSource.location),
  YesNoCriterion(
      'acc',
      'Access',
      'Wheelchair',
      'Any',
      'Do you need wheelchair access?',
      FoodSource.accessible),
]
