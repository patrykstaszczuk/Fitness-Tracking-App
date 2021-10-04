from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from django.urls import reverse

from recipe.models import Recipe, Ingredient, Unit
from meals_tracker import models, services, selectors
from recipe import services as recipe_services
from django.utils.text import slugify
import datetime

DAILY_MEALS_TRACKER = reverse('meals_tracker:meal-list')
DAILY_MEALS_TRACKER_CREATE = reverse('meals_tracker:meal-create')


def get_meal_delete_view(meal_id):
    """ reverse to meal detail view """
    return reverse('meals_tracker:meal-delete', kwargs={'pk': meal_id})


def get_meal_update_view(meal_id):
    """ reverse to meal update view """
    return reverse('meals_tracker:meal-update', kwargs={'pk': meal_id})


def sample_recipe(user, name='test', portions=4, **kwargs):
    """ create sample recipe """
    slug = slugify(name)
    return Recipe.objects.create(user=user, name=name, slug=slug, portions=portions, **kwargs)


def sample_ingredient(**kwargs):
    user = kwargs.pop('user')
    name = kwargs.pop('name')
    slug = slugify(name)
    return Ingredient.objects.create(user=user, name=name, slug=slug, **kwargs)


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
        gender='Male'
    )


class MealsTrackerApiTests(TestCase):
    """ test features available for authenticated users """

    def setUp(self):

        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='testname',
            password='testpass',
            height=188,
            weight=85,
            age=25,
            gender='Male'
        )
        self.category = sample_category()
        self.unit = Unit.objects.create(name='gram')
        self.today = datetime.date.today()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(
            user=self.user, name='self.test', calories=1000)

    def test_retreiving_available_dates_where_any_meals_was_saved(self):
        models.Meal.objects.create(
            user=self.user, category=self.category, date='2021-10-03')
        models.Meal.objects.create(
            user=self.user, category=self.category, date='2021-10-04')
        models.Meal.objects.create(
            user=self.user, category=self.category, date='2021-10-05')

        url = reverse('meals_tracker:meal-available-dates')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)

    def test_retrieve_meals_summary(self):
        """ test retrieving meals consumed in given day """

        recipe = sample_recipe(user=self.user, name='test')
        ingredient = sample_ingredient(user=self.user, name='Cukinia',
                                       calories=100)
        meal = models.Meal.objects.create(
            user=self.user, category=self.category)
        meal.recipes.add(recipe, through_defaults={'portion': 1})
        meal.ingredients.add(ingredient, through_defaults={
                             "unit": self.unit, "amount": 50})
        res = self.client.get(DAILY_MEALS_TRACKER, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('recipes', res.data[0])
        self.assertEqual(res.data[0]['calories'],
                         recipe.calories/5 + ingredient.calories/2)

    def test_retrieve_meals_only_for_given_user(self):
        """ test user's meals separation """

        user2 = sample_user()

        recipe1 = Recipe.objects.create(
            user=self.user, name='test', slug='test')
        recipe2 = Recipe.objects.create(user=user2, name='test', slug='test')

        meal = models.Meal.objects.create(
            user=self.user, category=self.category)
        meal.recipes.add(recipe1, through_defaults={'portion': 1})
        meal = models.Meal.objects.create(user=user2, category=self.category)
        meal.recipes.add(recipe2, through_defaults={'portion': 1})
        res = self.client.get(DAILY_MEALS_TRACKER)
        self.assertEqual(len(res.data[0]['recipes']), 1)

    def test_retrieve_meals_summary_only_for_today(self):
        """ test retreving meals only for a given day """

        recipe = Recipe.objects.create(user=self.user, name='test', slug='test',
                                       calories=500, portions=5)
        meal = models.Meal.objects.create(
            user=self.user, category=self.category)
        meal.recipes.add(recipe, through_defaults={'portion': 1})
        meal = models.Meal.objects.create(user=self.user, category=self.category,
                                          date='2021-06-06')
        meal.recipes.add(recipe, through_defaults={'portion': 1})
        res = self.client.get(DAILY_MEALS_TRACKER, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_listing_all_date_where_meals_was_saved(self):
        """ test listing dates where there was a meal inserted """

        meal1 = models.Meal.objects.create(user=self.user, category=self.category,
                                           date='2021-03-25')
        meal1.recipes.add(self.recipe, through_defaults={'portion': 1})
        meal2 = models.Meal.objects.create(user=self.user, category=self.category,
                                           date='2021-06-06')
        meal2.recipes.add(self.recipe, through_defaults={'portion': 1})
        url = reverse("meals_tracker:meal-available-dates")
        res = self.client.get(url, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        dates = [d['date'] for d in res.data]
        self.assertIn(meal1.date, dates)
        self.assertIn(meal2.date, dates)

    def test_retrieve_meals_summary_for_given_day(self):
        """ test retrieving meals for specified day """

        recipe = Recipe.objects.create(user=self.user, name='test', slug='test',
                                       calories=500, portions=5)
        meal = models.Meal.objects.create(
            user=self.user, category=self.category)
        meal.recipes.add(recipe, through_defaults={'portion': 1})
        meal = models.Meal.objects.create(user=self.user, category=self.category,
                                          date='2021-06-06')
        meal.recipes.add(recipe, through_defaults={'portion': 1})
        payload = {
            'date': "2021-06-06"
        }
        res = self.client.get(DAILY_MEALS_TRACKER, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(meal.id, res.data[0]['id'])

    def test_retrieve_meals_with_bad_date_param_failed(self):
        """ test retreiving meals with invalida date param """

        recipe = Recipe.objects.create(user=self.user, name='test', slug='test',
                                       calories=500, portions=5)
        meal = models.Meal.objects.create(
            user=self.user, category=self.category)
        meal.recipes.add(recipe, through_defaults={'portion': 1})
        meal = models.Meal.objects.create(user=self.user, category=self.category,
                                          date='2021-06-06')
        meal.recipes.add(recipe, through_defaults={'portion': 1})
        payload = {
            'date': "invalid format"
        }
        res = self.client.get(DAILY_MEALS_TRACKER, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_meals_for_date_in_future_failed(self):
        """ test retrieving meals for date in future returns none """
        today = datetime.datetime.today() + datetime.timedelta(days=10)
        payload = {
            "date": today
        }
        res = self.client.get(DAILY_MEALS_TRACKER, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrevig_recipe_detail_from_meals_summary_response(self):
        """ test retrieving all information about recipe added to meal """

        recipe = sample_recipe(user=self.user, name='Golabki', calories=1000)

        meal = models.Meal.objects.create(user=self.user,
                                          category=self.category)
        meal.recipes.add(recipe, through_defaults={'portion': 1})
        res = self.client.get(DAILY_MEALS_TRACKER)
        self.assertEqual(recipe.name, res.data[0]['recipes'][0]['name'])

    def test_create_meal_from_one_recipe(self):

        recipe = sample_recipe(user=self.user, portions=4)
        ingredient = sample_ingredient(user=self.user, name='jajko',
                                       calories=100)
        recipe.ingredients.add(ingredient,
                               through_defaults={'unit': self.unit,
                                                 'amount': 200})

        payload = {
            'category': self.category.id,
            'recipes': [
                {
                    'recipe': recipe.id,
                    'portion': 1
                }
            ],
        }
        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data[0]['calories'], 50)

    def test_create_meal_from_two_recipes(self):

        recipe = sample_recipe(user=self.user, portions=4)
        recipe2 = sample_recipe(user=self.user, name='dwa', portions=4)
        ingredient = sample_ingredient(user=self.user, name='jajko',
                                       calories=100)
        recipe.ingredients.add(ingredient,
                               through_defaults={'unit': self.unit,
                                                 'amount': 200})
        recipe2.ingredients.add(ingredient,
                                through_defaults={'unit': self.unit,
                                                  'amount': 400})

        payload = {
            'category': self.category.id,
            'recipes': [
                {
                    'recipe': recipe.id,
                    'portion': 1
                },
                {
                    'recipe': recipe2.id,
                    'portion': 1
                }
            ],
        }
        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data[0]['calories'], 150)

    def test_create_meal_from_non_own_recipe_nor_group_recipe_failed(self):

        user2 = sample_user()
        recipe = sample_recipe(user=user2, portions=4)

        ingredient = sample_ingredient(user=self.user, name='jajko',
                                       calories=100)
        recipe.ingredients.add(ingredient,
                               through_defaults={'unit': self.unit,
                                                 'amount': 200})

        payload = {
            'category': self.category.id,
            'recipes': [
                {
                    'recipe': recipe.id,
                    'portion': 1
                }
            ],
        }
        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_meal_from_recipe_created_by_other_user_in_group(self):

        user2 = sample_user()
        recipe = sample_recipe(user=user2, portions=4)
        self.user.membership.add(user2.own_group)

        ingredient = sample_ingredient(user=self.user, name='jajko',
                                       calories=100)
        recipe.ingredients.add(ingredient,
                               through_defaults={'unit': self.unit,
                                                 'amount': 200})

        payload = {
            'category': self.category.id,
            'recipes': [
                {
                    'recipe': recipe.id,
                    'portion': 1
                }
            ],
        }
        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data[0]['calories'], 50)

    def test_create_meal_from_ingredient(self):

        ingredient = sample_ingredient(name='jajko', user=self.user,
                                       calories='100')

        payload = {
            'category': self.category.id,
            'ingredients': [
                {
                    'ingredient': ingredient.id,
                    'unit': self.unit.id,
                    'amount': 200
                }
            ]}

        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        meal = models.Meal.objects.filter(user=self.user)
        self.assertEqual(len(meal), 1)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data[0]['calories'], 200)

    def test_create_meal_from_recipe_and_ingredient(self):
        """ test createing meal with recipe and extra ingredient """
        recipe = sample_recipe(user=self.user, name='Danie', portions=4)
        recipe.ingredients.add(sample_ingredient(user=self.user,
                                                 name='Jajko',
                                                 calories=100), through_defaults={"unit":
                                                                                  self.unit,
                                                                                  "amount": 200})

        ingredient = sample_ingredient(user=self.user, name='Cukinia',
                                       calories=80)
        payload = {
            "category": self.category.id,
            "recipes": [{"recipe": recipe.id, "portion": 1}],
            "ingredients": [{"ingredient": ingredient.id,
                             "unit": self.unit.id, "amount": 100}]
        }
        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data[0]['calories'],
                         recipe.calories/4 + ingredient.calories)

    def test_calculate_calories_based_on_portion_of_recipe(self):
        """ test calculating calories from provided recipe with quantity """
        ing = sample_ingredient(
            user=self.user, name='Cukinia', calories='1000')
        recipe = sample_recipe(user=self.user, portions=4)
        recipe.ingredients.add(ing, through_defaults={'unit': self.unit,
                                                      'amount': 100})
        meal = models.Meal.objects.create(user=self.user,
                                          category=self.category,)
        meal.recipes.add(recipe, through_defaults={'portion': 1})

        res = self.client.get(DAILY_MEALS_TRACKER)
        self.assertEqual(res.data[0]['calories'], 250)

    def test_create_meal_without_category_failed(self):
        """ test creating meal without category failed """

        recipe = sample_recipe(user=self.user, calories=1000, portions=4)

        payload = {
            'recipe': [{'recipe': recipe.id, 'portion': 1}],
        }

        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_meal_without_portions_failed(self):
        """ test creating meal with recipe without recipe portions failed """

        recipe = sample_recipe(user=self.user, calories=1000, portions=4)

        payload = {
            'category': self.category.id,
            'recipes': [{'recipe': recipe.id}],
        }

        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_meal_with_portion_set_to_0_failed(self):
        """ test creating meal with recipe portion set to 0 failed """

        recipe = sample_recipe(user=self.user, calories=1000, portions=4)

        payload = {
            'category': self.category.id,
            'recipes': [{'recipe': recipe.id, 'portion': 0}],
            'recipe_portions': 0
        }

        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_meal_with_bad_recipe_id_failed(self):
        """ test creating meal with invalid recipe id failed """

        payload = {
            'category': self.category.id,
            'recipes': [
                {
                    'recipe': 1,
                    'portion': 1
                }
            ]
        }

        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_meal_with_invalid_ingredient(self):
        """ test creating meal with invalid ingredient id """
        ingredient = sample_ingredient(user=self.user, name='test')
        payload = {
            "category": self.category.id,
            "ingredients": [{"ingredient": ingredient.id, "amount": 200,
                             "unit": self.unit.id}]
        }
        ingredient.delete()
        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_meal_with_ingredient_without_amount(self):
        """ test creating meal based on ingredient without amount """

        ingredient = sample_ingredient(user=self.user, name='Test')
        payload = {
            "category": self.category.id,
            "ingredients": [{"ingredient": ingredient.id,
                             "unit": self.unit.id}]
        }
        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_meal_with_ingredient_without_unit(self):
        """ test creating meal based on ingredient without amount """

        ingredient = sample_ingredient(user=self.user, name='Test')
        payload = {
            "category": self.category.id,
            "ingredients": [{"ingredient": ingredient.id, "amount": 200}]
        }
        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_meal_with_ingredient_and_invalid_unit(self):
        """ test creating meal with invalid ingredient unit """
        ingredient = sample_ingredient(user=self.user, name='Test')
        payload = {
            "category": self.category.id,
            "ingredients": [{"ingredient": ingredient.id, "amount": 200,
                             "unit": "string"}]
        }
        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_meal_with_ingredient_created_by_other_user(self):
        """ test creating meal with ingredient created by other user """
        user2 = sample_user()
        ingredient = sample_ingredient(user=user2, name='test')

        payload = {
            "category": self.category.id,
            "ingredients": [{"ingredient": ingredient.id, "amount": 200,
                             "unit": self.unit.id}]
        }
        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_meal_with_invalid_category_id(self):
        """ test creating meal failed becouse invalid id """

        payload = {
            'category': 10,
        }

        res = self.client.post(
            DAILY_MEALS_TRACKER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_full_update_meal_success(self):

        user2 = sample_user()
        self.user.membership.add(user2.own_group)
        recipe1 = sample_recipe(user=self.user, name='old recipe')
        recipe2 = sample_recipe(user=user2, name='new recipe')
        ing = sample_ingredient(user=self.user, name='test', calories=100)
        recipe2.ingredients.add(ing, through_defaults={'unit': self.unit,
                                                       'amount': 100})
        new_category = sample_category(name='Dinner')

        meal = models.Meal.objects.create(user=self.user,
                                          category=self.category)
        meal.recipes.add(recipe1, through_defaults={'portion': 1})

        payload = {
            'category': new_category.id,
            'recipes': [{'recipe': recipe2.id, 'portion': 2}, ],
        }
        res = self.client.put(get_meal_update_view(meal.id), payload,
                              format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = res._headers['location'][1]
        res = self.client.get(url)
        meal.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(new_category, meal.category)
        self.assertEqual(res.data[0]['calories'], 50)
        self.assertNotIn(recipe1, meal.recipes.all())

    def test_full_update_meal_success_with_new_ingredient(self):
        """ put update with new recipe and ingredient, recipe has no
        ingredients -> 0 calories"""
        recipe1 = sample_recipe(user=self.user, name='test')
        recipe2 = sample_recipe(user=self.user, name='test2')
        ingredient = sample_ingredient(user=self.user, name='Skladnik',
                                       calories=500)
        meal = models.Meal.objects.create(user=self.user,
                                          category=self.category)
        meal.recipes.add(recipe1, through_defaults={'portion': 1})
        new_category = sample_category(name='Dinner')
        payload = {
            'category': new_category.id,
            'recipes': [{'recipe': recipe2.id, 'portion': 2}],
            'ingredients': [{"ingredient": ingredient.id, "unit": self.unit.id,
                             "amount": 200}]
        }
        res = self.client.put(get_meal_update_view(meal.id), payload,
                              format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        meal.refresh_from_db()
        self.assertEqual(new_category, meal.category)
        self.assertEqual(meal.calories, 1000)
        self.assertIn(recipe2, meal.recipes.all())
        self.assertIn(ingredient, meal.ingredients.all())
        self.assertNotIn(recipe1, meal.recipes.all())

    def test_full_update_without_category_failed(self):
        recipe1 = sample_recipe(user=self.user, name='test')
        recipe2 = sample_recipe(user=self.user, name='test2')
        meal = models.Meal.objects.create(user=self.user,
                                          category=self.category)
        meal.recipes.add(recipe1, through_defaults={'portion': 1})
        payload = {
            'recipes': [{'recipe': recipe2.id, 'portion': 2}],
        }
        res = self.client.put(get_meal_update_view(meal.id), payload,
                              format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_meal_success(self):
        """ test updating only part of the meal """

        recipe = sample_recipe(self.user, calories=400, portions=4)
        ingredient = sample_ingredient(user=self.user, name='Cukinia',
                                       calories=100)
        meal = models.Meal.objects.create(
            user=self.user,
            category=self.category
            )
        meal.recipes.add(recipe, through_defaults={'portion': 1})

        payload = {
            'ingredients': [{'ingredient': ingredient.id,
                             "unit": self.unit.id, "amount": 200}]
        }
        res = self.client.patch(get_meal_update_view(meal.id), payload,
                                format='json')
        meal.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(meal.recipes.all()), 1)
        self.assertEqual(len(meal.ingredients.all()), 1)
        self.assertEqual(meal.calories, 300)

    def test_other_user_meal_update_failed(self):
        """ test users separation """

        user2 = sample_user()
        meal1 = models.Meal.objects.create(user=user2, category=self.category)

        payload = {
            'recipes': [{
                'recipe': sample_recipe(user=self.user).id,
                'portion': 2
            }]
        }

        res = self.client.patch(get_meal_update_view(meal1.id), payload,
                                format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_meal_with_invalid_recipe(self):
        """ test udpating recipe with other user recipe id """

        user2 = sample_user()
        recipe = sample_recipe(user=user2)

        meal = models.Meal.objects.create(
            user=self.user,
            category=self.category)

        payload = {
            'recipes': [{
                'recipe': recipe.id,
                'portion': 2
            }]
        }
        res = self.client.patch(get_meal_update_view(meal.id), payload,
                                format='json')
        meal.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_with_invalid_ingredient(self):
        """ test updating with invalid ingredient failed """

        recipe = sample_recipe(user=self.user)
        ingredient = sample_ingredient(user=self.user, calories=1000,
                                       name='test')

        meal = models.Meal.objects.create(
            user=self.user,
            category=self.category)
        meal.recipes.add(recipe, through_defaults={'portion': 2})
        meal.ingredients.add(ingredient, through_defaults={
                             "unit": self.unit, "amount": 100})

        payload = {
            'ingredients': [{
                'ingredient': 11111,
                'unit': 2,
                'amount': 22
            }]
        }
        res = self.client.patch(get_meal_update_view(meal.id), payload,
                                format='json')
        meal.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_meal_success(self):
        """ test deleting meal success """

        meal = models.Meal.objects.create(
            user=self.user,
            category=self.category)

        res = self.client.delete(get_meal_delete_view(meal.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_other_user_meal_failed(self):
        """ test deleting other user meal failed """

        user2 = sample_user()
        meal = models.Meal.objects.create(
            user=user2,
            category=self.category
        )

        res = self.client.delete(get_meal_delete_view(meal.id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_retreiving_available_categories(self):
        """ test retrieving all meal categories """

        sample_category(name='Dinner')
        sample_category(name='Supper')
        url = reverse('meals_tracker:categories')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)
