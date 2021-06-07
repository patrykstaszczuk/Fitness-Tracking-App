from django.test import TestCase
from django.contrib.auth import get_user_model
from meals_tracker import models
import datetime


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

        meal = models.Meal.objects.create(user=self.user, name='test')

        self.assertEqual(str(meal), f'{meal.user} + {meal.date} + {meal.name}')
