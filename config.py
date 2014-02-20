
from criterion import Criterion, LocationCriterion, YesNoCriterion 
from models import FoodSource


FOOD_CRITERIA = [
#  LocationCriterion('loc', 'Location', FoodSource.location),
#  MealCriterion('Meal'),
  YesNoCriterion(
      'acc',
      'Access',
      'Wheelchair',
      'Any',
      'Do you need wheelchair access?',
      FoodSource.accessible),
#  OrderByNextMealCriterion(),
]
