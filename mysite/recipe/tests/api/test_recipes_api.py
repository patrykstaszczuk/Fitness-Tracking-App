from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from recipe.models import Recipe, Recipe_Ingredient
from rest_framework.test import APIClient
from rest_framework import status
from recipe import selectors

RECIPE_CREATE = reverse('recipe:recipe-create')
INGREDIENT_CREATE = reverse('recipe:ingredient-create')
TAG_CREATE = reverse('recipe:tag-create')


def group_recipe_url(slug: str, id: int) -> str:
    return reverse('recipe:group-recipe-detail', kwargs={'slug': slug, 'pk': id})


def recipe_detail_url(slug: str) -> str:
    return reverse('recipe:recipe-detail', kwargs={'slug': slug})


def recipe_tags_url(slug: str) -> str:
    return reverse('recipe:recipe-tags', kwargs={'slug': slug})


def recipe_ingredients_url(slug: str) -> str:
    return reverse('recipe:recipe-ingredients', kwargs={'slug': slug})


def recipe_ingredients_detail_url(slug: str, id: int) -> str:
    return reverse('recipe:recipe-ingredients-update', kwargs={'slug': slug, 'pk': id})


def ingredient_unit_mapping_url(slug: str) -> None:
    return reverse('recipe:ingredient-units', kwargs={'slug': slug})


class RecipeApiTests(TestCase):

    def setUp(self):
        self.auth_user = get_user_model().objects.create_user(
            email='auth@gmail.com',
            name='auth',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,

        )
        self.client = APIClient()
        self.client.force_authenticate(self.auth_user)

    def _create_recipe(self) -> str:
        payload = {
            'name': 'recipe',
            'portions': 3,
            'prepare_time': 45,
            'description': 'sth'
            }
        res = self.client.post(RECIPE_CREATE, payload)
        url = res._headers['location'][1]
        recipe_slug = self.client.get(url).data['slug']
        return recipe_slug

    def _create_ingredient(self, name: str = 'test ing') -> dict:
        payload = {
            'name': name,
            'calories': 500,
            }
        res = self.client.post(INGREDIENT_CREATE, payload)
        url = res._headers['location'][1]
        return self.client.get(url).data

    def _create_tag(self, name: str = 'test tag') -> dict:
        payload = {
            'name': name
        }
        res = self.client.post(TAG_CREATE, payload)
        url = res._headers['location'][1]
        return self.client.get(url).data

    def _create_recipe_with_ingredient(self) -> tuple:
        recipe_slug = self._create_recipe()
        ingredient1 = self._create_ingredient(name='test1')
        unit = selectors.unit_get_default()

        payload = {
            'unit_id': unit.id,
            'grams_in_one_unit': 100,
        }
        self.client.post(ingredient_unit_mapping_url(
            ingredient1['slug']), payload)

        payload = {
            'ingredients': [
                {
                    'ingredient': ingredient1['id'],
                    'amount': 100,
                    'unit': unit.id
                }]
            }
        res = self.client.post(recipe_ingredients_url(
            recipe_slug), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return recipe_slug, ingredient1['id'], unit.id

    def test_unauthenticated_user_return_401(self) -> None:
        unauth_client = APIClient()
        res = unauth_client.post(RECIPE_CREATE, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_recipe_success(self) -> None:
        payload = {
            'name': 'recipe',
            'portions': 3,
            'prepare_time': 45,
            'description': 'sth'
            }
        res = self.client.post(RECIPE_CREATE, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('location', res._headers)
        assert res._headers['location'][1]

    def test_create_recipe_no_requried_fields_failed(self) -> None:
        res = self.client.post(RECIPE_CREATE, {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recipe_success(self) -> None:
        recipe_slug = self._create_recipe()
        payload = {
            'portions': 10,
            }
        res = self.client.put(recipe_detail_url(recipe_slug), payload)
        url = res._headers['location'][1]
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.get(url)
        self.assertEqual(res.data['portions'], payload['portions'])

    def test_adding_tags_to_recipe(self) -> None:
        recipe_slug = self._create_recipe()
        tag1 = self._create_tag(name='tag')
        tag2 = self._create_tag(name='tag2')
        payload = {
            'tag_ids': [tag1['id'], tag2['id']]
        }
        res = self.client.post(recipe_tags_url(recipe_slug), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_adding_non_existing_tags_to_recipe_failed(self) -> None:
        recipe_slug = self._create_recipe()
        payload = {
            'tag_ids': [1, 2, 3]
        }
        res = self.client.post(recipe_tags_url(recipe_slug), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adding_ingredient_to_recipe_success(self) -> None:
        recipe_slug = self._create_recipe()
        ingredient1 = self._create_ingredient(name='test1')
        ingredient2 = self._create_ingredient(name='test2')
        unit = selectors.unit_get_default()
        payload = {
            'ingredients': [
                {
                    'ingredient': ingredient1['id'],
                    'amount': 100,
                    'unit': unit.id
                },
                {
                    'ingredient': ingredient2['id'],
                    'amount': 2,
                    'unit': unit.id
                }]
            }
        res = self.client.post(recipe_ingredients_url(
            recipe_slug), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Recipe.objects.get(
            slug=recipe_slug).ingredients.all().count(), 2)

    def test_adding_non_existing_ingredient_to_recipe_failed(self) -> None:
        recipe_slug = self._create_recipe()
        payload = {
            'ingredients': [
                {
                    'ingredient': 1,
                    'amount': 100,
                    'unit': 1,
                }]
            }
        res = self.client.post(recipe_ingredients_url(
            recipe_slug), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_removing_ingredient_from_recipe_success(self) -> None:
        recipe_slug, ingredient_id, unit_id = self._create_recipe_with_ingredient()
        self.assertEqual(Recipe.objects.get(
            slug=recipe_slug).ingredients.all().count(), 1)
        payload = {
            'ingredient_ids': [ingredient_id, ]
        }
        self.client.delete(recipe_ingredients_url(recipe_slug), payload)
        self.assertEqual(Recipe.objects.get(
            slug=recipe_slug).ingredients.all().count(), 0)

    def test_updating_recipe_ingredient_success(self) -> None:
        recipe_slug, ingredient_id, unit_id = self._create_recipe_with_ingredient()
        payload = {
            'unit': unit_id,
            'amount': 333,
        }
        res = self.client.put(recipe_ingredients_detail_url(
            recipe_slug, ingredient_id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Recipe_Ingredient.objects.get(
            recipe__slug=recipe_slug, ingredient__id=ingredient_id).amount, payload['amount'])

    def test_retreving_group_recipe_success(self) -> None:
        user2 = get_user_model().objects.create_user(
            email='auth2@gmail.com',
            name='auth2',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,

        )
        self.client2 = APIClient()
        self.client2.force_authenticate(user2)
        user2.own_group.members.add(self.auth_user)
        payload = {
            'name': 'user2 recipe',
            'portions': 3,
            'prepare_time': 45,
            'description': 'sth'
            }
        res = self.client2.post(RECIPE_CREATE, payload)
        url = res._headers['location'][1]
        recipe_slug = self.client2.get(url).data['slug']

        res = self.client.get(group_recipe_url(recipe_slug, user2.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieving_group_recipe_not_group_member_failed(self) -> None:
        user2 = get_user_model().objects.create_user(
            email='auth2@gmail.com',
            name='auth2',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,

        )
        self.client2 = APIClient()
        self.client2.force_authenticate(user2)
        payload = {
            'name': 'user2 recipe',
            'portions': 3,
            'prepare_time': 45,
            'description': 'sth'
            }
        res = self.client2.post(RECIPE_CREATE, payload)
        url = res._headers['location'][1]
        recipe_slug = self.client2.get(url).data['slug']

        res = self.client.get(group_recipe_url(recipe_slug, user2.id))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
