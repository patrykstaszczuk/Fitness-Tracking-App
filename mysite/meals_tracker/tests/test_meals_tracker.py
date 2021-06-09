from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from django.urls import reverse

from recipe.models import Recipe
from recipe.serializers import RecipeSerializer
from meals_tracker import models

from meals_tracker.serializers import MealsTrackerSerializer

import datetime

DAILY_MEALS_TRACKER = reverse('meals_tracker:meal-list')


def get_meal_detail_view(meal_id):
    """ reverse to meal detail view """
    return reverse('meals_tracker:meal-detail', kwargs={'id': meal_id})


def sample_recipe(user, name='test', calories=0, **kwargs):
    """ create sample recipe """
    return Recipe.objects.create(
        user=user,
        name=name,
        calories=calories,
        **kwargs
    )


def sample_category(name='Breakfast'):
    """ create sample category """
    return models.MealCategory.objects.create(name=name)


def sample_user():
    """ create another user """
    return get_user_model().objects.create_user(
        email='test2@gmail.com',
        name='testname2',
        password='testpass',
        height=188,
        weight=85,
        age=25,
        sex='Male'
    )


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
        self.today = datetime.date.today()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_meals_summary(self):
        """ test retrieving meals consumed in given day """

        recipe = Recipe.objects.create(user=self.user, name='test',
                                       calories=1000)
        models.Meal.objects.create(user=self.user, recipe=recipe,
                                   recipe_portions=1, category=self.category)
        meals = models.Meal.objects.filter(user=self.user, date=self.today)
        serializer = MealsTrackerSerializer(meals, many=True)
        res = self.client.get(DAILY_MEALS_TRACKER, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_meals_only_for_given_user(self):
        """ test user's meals separation """

        user2 = sample_user()

        recipe1 = Recipe.objects.create(user=self.user, name='test')
        recipe2 = Recipe.objects.create(user=user2, name='test')

        models.Meal.objects.create(user=self.user, recipe=recipe1,
                                   recipe_portions=1, category=self.category)
        models.Meal.objects.create(user=user2, recipe=recipe1,
                                   recipe_portions=1, category=self.category)
        res = self.client.get(DAILY_MEALS_TRACKER)

        meal1 = models.Meal.objects.filter(user=self.user)
        meal2 = models.Meal.objects.filter(user=user2)
        serializer1 = MealsTrackerSerializer(meal1, many=True)
        serializer2 = MealsTrackerSerializer(meal2, many=True)
        self.assertEqual(len(res.data), 1)
        self.assertNotIn(res.data, serializer2.data)
        self.assertEqual(res.data, serializer1.data)

    def test_retrieve_meals_summary_only_for_today(self):
        """ test retreving meals only for a given day """

        recipe = Recipe.objects.create(user=self.user, name='test',
                                       calories=500, portions=5)
        models.Meal.objects.create(user=self.user, recipe=recipe,
                                   recipe_portions=1, category=self.category)
        models.Meal.objects.create(user=self.user, recipe=recipe,
                                   recipe_portions=1, category=self.category,
                                   date='2021-06-06')
        meals = models.Meal.objects.filter(user=self.user, date=self.today)
        old_meals = models.Meal.objects.filter(user=self.user, date='2021-06-06')
        serializer = MealsTrackerSerializer(meals, many=True)
        old_meal_serializer = MealsTrackerSerializer(old_meals, many=True)

        res = self.client.get(DAILY_MEALS_TRACKER, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(old_meal_serializer.data, res.data)
        self.assertEqual(serializer.data, res.data)

    def test_retrevig_recipe_detail_from_meals_summary_response(self):
        """ test retrieving all information about recipe added to meal """

        recipe = sample_recipe(user=self.user, name='Golabki', calories=1000)

        models.Meal.objects.create(user=self.user, recipe=recipe,
                                   recipe_portions=1, category=self.category)
        res = self.client.get(DAILY_MEALS_TRACKER)
        self.assertEqual(recipe.name, res.json()[0]['recipe_detail']['name'])
        self.assertEqual(recipe.calories,
                         res.json()[0]['recipe_detail']['calories'])

    def test_create_meal_from_one_recipe(self):
        """ test create meal from recipe """

        recipe = sample_recipe(user=self.user, calories=1000, portions=4)

        payload = {
            'category': self.category.id,
            'recipe': recipe.id,
            'recipe_portions': 1
        }
        res = self.client.post(DAILY_MEALS_TRACKER, payload, format='json')
        meal = models.Meal.objects.filter(user=self.user) \
            .get(category=self.category)
        serializer = MealsTrackerSerializer(meal)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data, serializer.data)

    def test_calculate_calories_based_on_portion_of_recipe(self):
        """ test calculating calories from provided recipe with quantity """

        recipe = sample_recipe(user=self.user, calories=1000, portions=4)

        models.Meal.objects.create(user=self.user, recipe=recipe,
                                   category=self.category,
                                   recipe_portions=1)

        res = self.client.get(DAILY_MEALS_TRACKER)
        self.assertEqual(res.json()[0]['calories'], recipe.calories/4)

    def test_create_meal_without_category_failed(self):
        """ test creating meal without category failed """

        recipe = sample_recipe(user=self.user, calories=1000, portions=4)

        payload = {
            'recipe': recipe.id,
            'recipe_portions': 2,
        }

        res = self.client.post(DAILY_MEALS_TRACKER, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_meal_without_portions_failed(self):
        """ test creating meal with recipe without recipe portions failed """

        recipe = sample_recipe(user=self.user, calories=1000, portions=4)

        payload = {
            'category': self.category.id,
            'recipe': recipe.id,
        }

        res = self.client.post(DAILY_MEALS_TRACKER, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_meal_with_portion_set_to_0_failed(self):
        """ test creating meal with recipe portion set to 0 failed """

        recipe = sample_recipe(user=self.user, calories=1000, portions=4)

        payload = {
            'category': self.category.id,
            'recipe': recipe.id,
            'recipe_portions': 0
        }

        res = self.client.post(DAILY_MEALS_TRACKER, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_meal_with_bad_recipe_id_failed(self):
        """ test creating meal with invalid recipe id failed """

        payload = {
            'category': self.category.id,
            'recipe': 22,
            'recipe_portions': 10
        }

        res = self.client.post(DAILY_MEALS_TRACKER, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_meal_with_invalid_category_id(self):
        """ test creating meal failed becouse invalid id """

        payload = {
            'category': 10,
        }

        res = self.client.post(DAILY_MEALS_TRACKER, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_full_update_meal_success(self):
        """ test updating meal success """

        recipe1 = sample_recipe(user=self.user, name='test', calories=1000)
        recipe2 = sample_recipe(user=self.user, name='test2', calories=2000)
        new_category = sample_category(name='Dinner')

        meal = models.Meal.objects.create(user=self.user, recipe=recipe1,
                                          recipe_portions=1,
                                          category=self.category)

        payload = {
            'category': new_category.id,
            'recipe': recipe2.id,
            'recipe_portions': 2
        }
        res = self.client.put(get_meal_detail_view(meal.id), payload,
                              format='json')
        meal.refresh_from_db()
        serializer = MealsTrackerSerializer(meal)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_partial_update_meal_success(self):
        """ test updating only part of the meal """

        recipe = sample_recipe(self.user)
        meal = models.Meal.objects.create(
            user=self.user,
            recipe=recipe,
            recipe_portions=1,
            category=self.category
            )

        res = self.client.patch(get_meal_detail_view(meal.id),
                                {'recipe_portions': 2}, format='json')
        meal.refresh_from_db()
        serializer = MealsTrackerSerializer(meal)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_other_user_meal_update_failed(self):
        """ test users separation """

        user2 = sample_user()
        meal1 = models.Meal.objects.create(user=user2, category=self.category)

        payload = {
            'recipe': sample_recipe(user=self.user).id,
            'recipe_portions': 2
        }

        res = self.client.patch(get_meal_detail_view(meal1.id), payload,
                                format='json')
        meal1.refresh_from_db()
        serializer = MealsTrackerSerializer(meal1)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotEqual(res.data, serializer.data)

    def test_update_meal_with_invalid_recipe(self):
        """ test udpating recipe with other user recipe id """

        user2 = sample_user()
        recipe = sample_recipe(user=user2)

        meal = models.Meal.objects.create(
            user=self.user,
            category=self.category)

        payload = {
            'recipe': recipe.id,
            'recipe_portions': 2
        }
        res = self.client.patch(get_meal_detail_view(meal.id), payload,
                                format='json')
        meal.refresh_from_db()
        serializer = MealsTrackerSerializer(meal)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(res.data, serializer.data)
