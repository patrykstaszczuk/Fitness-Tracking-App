from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import force_authenticate
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.exceptions import NotFound
import datetime
from meals_tracker.models import MealCategory
import random
import string
from recipe.services import (
    CreateIngredientDto,
    CreateIngredient,
    CreateRecipe,
    CreateRecipeDto,
    AddIngredientsToRecipeDto,
    AddIngredientsToRecipe,
)
from recipe.models import Recipe, Ingredient, Unit

MEALS_API = reverse('meals_tracker:meal-create')


def meal_detail_url(id: int) -> reverse:
    return reverse('meals_tracker:meal-detail', kwargs={'pk': id})


def meal_recipes_url(id: int) -> reverse:
    return reverse('meals_tracker:meal-recipes', kwargs={'pk': id})


def meal_ingredients_url(id: int) -> reverse:
    return reverse('meals_tracker:meal-ingredients', kwargs={'pk': id})


def meal_recipes_detail_url(id: int, recipe_id: int) -> reverse:
    return reverse('meals_tracker:meal-recipes-detail', kwargs={'pk': id, 'recipe_pk': recipe_id})


def meal_ingredients_detail_url(id: int, ing_id: int) -> reverse:
    return reverse('meals_tracker:meal-ingredients-detail', kwargs={'pk': id, 'ingredient_pk': ing_id})


class RecipeApiTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='auth@gmail.com',
            name='auth',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,

        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @staticmethod
    def _create_ingredient(user: get_user_model, calories: int = 1000) -> Ingredient:
        name = ''.join(random.choices(string.ascii_letters, k=10))
        dto = CreateIngredientDto(user=user, name=name, calories=calories)
        return CreateIngredient().create(dto)

    def _create_recipe_with_ingredient(self, user: get_user_model) -> Recipe:
        name = ''.join(random.choices(string.ascii_letters, k=10))
        ingredient = self._create_ingredient(user)
        unit = ingredient.units.all()[0]
        dto = CreateRecipeDto(user=user, name=name,
                              portions=4, prepare_time=45)
        recipe = CreateRecipe().create(dto)
        dto = AddIngredientsToRecipeDto(
            user=user,
            ingredients=[{'ingredient': ingredient.id,
                          'unit': unit.id, 'amount': 100}]
        )
        AddIngredientsToRecipe().add(recipe, dto)
        return recipe

    @staticmethod
    def _create_category() -> None:
        return MealCategory.objects.get_or_create(name='breakfast')[0]

    def _create_meal(
            self,
            user: get_user_model,
            date: datetime = datetime.date.today()) -> None:
        recipe = self._create_recipe_with_ingredient(user)
        ingredient = self._create_ingredient(user=user)
        unit = ingredient.units.all()[0]
        payload = {
            'category': self._create_category().id,
            'date': date,
            'recipes': [{'recipe': recipe.id, 'portion': recipe.portions}],
        }
        res = self.client.post(MEALS_API, payload, format='json')
        url = res._headers['location'][1]
        res = self.client.get(url)
        return res.data

    def _add_ingredient_to_meal(self, meal_id: int) -> (Ingredient, Unit):
        ingredient = self._create_ingredient(self.user)
        unit = ingredient.units.all()[0]
        payload = {
            'ingredients': [{'ingredient': ingredient.id, 'unit': unit.id, 'amount': 100}]
        }
        self.client.post(meal_ingredients_url(
            meal_id), payload, format='json')
        return ingredient, unit

    def test_create_meal_success(self) -> None:
        recipe = self._create_recipe_with_ingredient(self.user)

        payload = {
            'category': self._create_category().id,
            'date': datetime.date.today(),
            'recipes': [{'recipe': recipe.id, 'portion': recipe.portions}]
        }
        res = self.client.post(MEALS_API, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data['calories'], recipe.calories)

    def test_create_meal_from_invalid_recipe_failed(self) -> None:
        payload = {
            'category': self._create_category().id,
            'date': datetime.date.today(),
            'recipes': [{'recipe': 1, 'portion': 4}]
        }
        res = self.client.post(MEALS_API, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listing_all_meals_for_today(self) -> None:
        meal = self._create_meal(self.user)
        meal2 = self._create_meal(self.user)
        res = self.client.get(MEALS_API)
        self.assertEqual(meal['id'], res.data[0]['id'])
        self.assertEqual(meal2['id'], res.data[1]['id'])

    def test_listing_meals_for_different_date_success(self) -> None:
        yesterday = datetime.date.today() - datetime.timedelta(1)
        meal = self._create_meal(self.user, yesterday)
        self._create_meal(self.user)
        res = self.client.get(MEALS_API + f'?date={yesterday}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], meal['id'])

    def test_retreving_meal_details(self) -> None:
        meal = self._create_meal(self.user)
        res = self.client.get(meal_detail_url(meal['id']))
        self.assertTrue(res.data.get('category'))

    def test_listing_meal_recipes(self) -> None:
        meal = self._create_meal(self.user)
        res = self.client.get(meal_recipes_url(meal['id']))
        self.assertEqual(res.data[0]['calories'], meal['calories'])

    def test_adding_recipe_to_meal(self) -> None:
        meal = self._create_meal(self.user)
        recipe = self._create_recipe_with_ingredient(self.user)
        payload = {
            'recipes': [{'recipe': recipe.id, 'portion': 4}]
        }
        res = self.client.post(meal_recipes_url(
            meal['id']), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.get(meal_detail_url(meal['id']))
        self.assertEqual(res.data['calories'],
                         recipe.calories + meal['calories'])

    def test_adding_ingredient_to_meal(self) -> None:
        meal = self._create_meal(self.user)
        ingredient = self._create_ingredient(self.user)
        unit = ingredient.units.all()[0]
        payload = {
            'ingredients': [{'ingredient': ingredient.id, 'unit': unit.id, 'amount': 100}]
        }
        res = self.client.post(meal_ingredients_url(
            meal['id']), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.get(meal_detail_url(meal['id']))
        self.assertEqual(res.data['calories'],
                         ingredient.calories + meal['calories'])

    def test_listing_meal_ingredients(self) -> None:
        meal = self._create_meal(self.user)
        ingredient = self._add_ingredient_to_meal(meal['id'])[0]
        res = self.client.get(meal_ingredients_url(meal['id']))
        self.assertEqual(res.data[0]['calories'], ingredient.calories)

    def test_updating_meal_recipe_success(self) -> None:
        meal = self._create_meal(self.user)
        res = self.client.get(meal['recipes'])
        recipe_id = res.data[0]['id']
        payload = {
            'portion': 1
        }
        res = self.client.put(meal_recipes_detail_url(
            meal['id'], recipe_id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.get(meal_detail_url(meal['id']))
        self.assertEqual(res.data['calories'], meal['calories']/4)

    def test_updating_meal_ingredient_success(self) -> None:
        meal = self._create_meal(self.user)
        ingredient, unit = self._add_ingredient_to_meal(meal['id'])
        expected_calories = meal['calories'] + ingredient.calories

        res = self.client.get(meal['ingredients'])
        meal_ingerdient_id = res.data[0]['id']

        payload = {
            'unit': unit.id,
            'amount': 200,
        }
        res = self.client.put(meal_ingredients_detail_url(
            meal['id'], meal_ingerdient_id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # amount of igredient incresed 2 times
        expected_calories += ingredient.calories
        res = self.client.get(meal_detail_url(meal['id']))
        self.assertEqual(res.data['calories'], expected_calories)

    def test_deleting_meal_recipe_success(self) -> None:
        meal = self._create_meal(self.user)
        res = self.client.get(meal['recipes'])
        recipe_id = res.data[0]['id']
        res = self.client.delete(
            meal_recipes_detail_url(meal['id'], recipe_id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.get(meal['recipes'])
        self.assertEqual(len(res.data), 0)

    def test_deleting_meal_ingredient_succes(self) -> None:
        meal = self._create_meal(self.user)
        ingredient, unit = self._add_ingredient_to_meal(meal['id'])
        res = self.client.get(meal['ingredients'])
        ingredient_id = res.data[0]['id']

        res = self.client.delete(
            meal_ingredients_detail_url(meal['id'], ingredient_id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.get(meal['ingredients'])
        self.assertEqual(len(res.data), 0)

    def test_deleting_meal_success(self) -> None:
        meal = self._create_meal(self.user)
        res = self.client.delete(meal_detail_url(meal['id']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.get(meal_detail_url(meal['id']))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
