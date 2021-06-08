from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from django.urls import reverse

from recipe.models import Recipe
from meals_tracker import models

from meals_tracker.serializers import MealsTrackerSerializer

DAILY_MEALS_TRACKER = reverse('meals_tracker:meal-list')


def sample_recipe(user, name='test', calories=0):
    """ create sample recipe """
    return Recipe.objects.create(user=user, name=name, calories=calories)


def sample_category(name='Breakfast'):
    """ create sample category """
    return models.MealCategory.objects.create(name=name)


class PrivateMealsTrackerApiTests(TestCase):
    """ test features available for authenticated users """

    def setUp(self):

        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='testname',
            password='testpass',
            height=188,
            weight=85,
            age=25,
            sex='Male'
        )
        self.category = sample_category()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_meals_summary(self):
        """ test retrieving meals consumed in given day """

        recipe = Recipe.objects.create(user=self.user, name='test',
                                       calories=1000)
        meal = models.Meal.objects.create(user=self.user, recipe=recipe)
        serializer = MealsTrackerSerializer(meal)
        res = self.client.get(DAILY_MEALS_TRACKER, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0], serializer.data)

    def test_retrieve_meals_summary_only_for_today(self):
        """ test retreving meals only for a given day """

        recipe = Recipe.objects.create(user=self.user, name='test',
                                       calories=500)
        meal = models.Meal.objects.create(user=self.user, recipe=recipe)
        old_meal = models.Meal.objects.create(user=self.user, recipe=recipe,
                                              date='2021-06-06')

        serializer = MealsTrackerSerializer(meal)
        old_meal_serializer = MealsTrackerSerializer(old_meal)

        res = self.client.get(DAILY_MEALS_TRACKER, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(old_meal_serializer.data, res.data)
        self.assertEqual(res.data[0], serializer.data)

    def test_retrevig_recipe_detail_from_meals_summary_response(self):
        """ test retrieving all information about recipe added to meal """

        recipe = sample_recipe(user=self.user, name='Golabki', calories=1000)

        models.Meal.objects.create(user=self.user, recipe=recipe)
        res = self.client.get(DAILY_MEALS_TRACKER)
        print(res.json())
        self.assertIn(recipe.name, res.json()[0]['recipe_detail'])
        self.assertIn(recipe.calories, res.json()[0]['recipe_Detail'])

    def test_create_meal_from_one_recipe(self):
        """ test create meal from recipe """

        recipe = sample_recipe(user=self.user, calories=1000)

        payload = {
            'category': self.category.id,
            'recipe': recipe.id,
            'quantity': 1
        }
        res = self.client.post(DAILY_MEALS_TRACKER, payload, format='json')
        meal = models.Meal.objects.filter(user=self.user) \
            .get(category=self.category)
        serializer = MealsTrackerSerializer(meal)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data, serializer.data)

    # def test_create_meal_from_more_then_one_recipe(self):
