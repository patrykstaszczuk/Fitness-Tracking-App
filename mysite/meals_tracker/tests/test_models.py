from django.test import TestCase
from django.contrib.auth import get_user_model
from meals_tracker import models
from recipe.models import Recipe
import datetime


def sample_recipe(user, name='testrecipe', calories=1000):
    """ create sample recipe """
    return Recipe.objects.create(
        user=user,
        name=name,
        calories=calories,
    )


def sample_category():
    """ create sample category """
    return models.MealCategory.objects.create(name='breakfast')


class MealModelTestCase(TestCase):
    """ tests for meal model """

    def setUp(self):
        self.user = get_user_model().objects.create(
            email='test@gmail.com',
            name='testname',
            password='testpass',
            height=188,
            weight=85,
            age=25,
            sex='Male'
        )
        self.now = datetime.date.today()

    def test_meal_str(self):
        """ test string representation of meal model """

        meal = models.Meal.objects.create(user=self.user,
                                          category=sample_category())

        self.assertEqual(str(meal), f'{meal.user} + {meal.date}')

    def test_auto_calories_calculation_based_on_recipe(self):
        """ test auto calories calculation from recipe """

        recipe = sample_recipe(user=self.user)

        meal = models.Meal.objects.create(user=self.user,
                                          recipe=recipe,
                                          recipe_portions=1,
                                          category=sample_category())
        self.assertEqual(recipe.calories, meal.calories)

    def test_meal_category_str(self):
        """ test string representation of meal category """

        category = models.MealCategory.objects.create(name='Breakfast')

        self.assertEqual(str(category), category.name)

    def test_retrieve_category_of_meal(self):
        """ test retreving category from field """

        breakfast = models.MealCategory.objects.create(name='Breakfast')
        meal = models.Meal.objects.create(user=self.user, category=breakfast)

        self.assertEqual(breakfast, meal.category)
