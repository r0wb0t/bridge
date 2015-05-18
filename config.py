
from criterion import Criterion, LocationCriterion, YesNoCriterion 
from models import FoodSource


FOOD_CRITERIA = [
  LocationCriterion('loc', 'Location', FoodSource.location),
  YesNoCriterion(
      slug = 'acc',
      title = 'Access',
      yes_desc = 'Wheelchair',
      no_desc = 'Any',
      question = 'Do you need wheelchair access?',
      bool_prop = FoodSource.accessible,
      default = False),
  YesNoCriterion(
      slug = 'age',
      title = 'Age',
      yes_desc = '60+',
      no_desc = 'Under 60',
      question = 'Are you 60 or older?',
      bool_prop = FoodSource.sixty_plus,
      dominant = False),
]
