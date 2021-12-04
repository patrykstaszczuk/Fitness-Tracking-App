from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from recipe.models import Unit


INGREDIENT_CREATE = reverse('recipe:ingredient-create')
TAG_CREATE = reverse('recipe:tag-create')


def ingredient_detail_url(slug: str) -> str:
    return reverse('recipe:ingredient-detail', kwargs={'slug': slug})


def ingredient_tags_url(slug: str) -> str:
    return reverse('recipe:ingredient-tags', kwargs={'slug': slug})


def ingredient_units_url(slug: str) -> str:
    return reverse('recipe:ingredient-units', kwargs={'slug': slug})


class IngredientApiTests(TestCase):

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

    def _create_ingredient(self, name: str = 'ingredient') -> dict:
        payload = {
            'name': name,
            'calories': 100,
        }
        res = self.client.post(INGREDIENT_CREATE, payload)
        url = res._headers['location'][1]
        res = self.client.get(url)
        return res.data

    def _create_tag(self, name: str = 'test tag') -> dict:
        payload = {
            'name': name
        }
        res = self.client.post(TAG_CREATE, payload)
        url = res._headers['location'][1]
        return self.client.get(url).data

    def test_unauthenticated_user_return_401(self) -> None:
        unauth_user = APIClient()
        res = unauth_user.post(INGREDIENT_CREATE, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_ingredient_success(self) -> None:
        payload = {
            'name': 'ingredient',
            'ready_meal': True,
            'calories': 100,
        }
        res = self.client.post(INGREDIENT_CREATE, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data['name'], payload['name'])

    def test_create_ingredient_invalid_value_failed(self) -> None:
        payload = {
            'name': 'ingredient',
            'calories': -100,
        }
        res = self.client.post(INGREDIENT_CREATE, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_updating_ingredient_success(self) -> None:
        ingredient = self._create_ingredient()
        payload = {
            'name': 'new name for ingredient',
        }
        res = self.client.put(ingredient_detail_url(
            slug=ingredient['slug']), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data['name'], payload['name'])

    def test_updating_ingredient_name_already_exists_failed(self) -> None:
        ingredient = self._create_ingredient()
        ingredient2 = self._create_ingredient(name='ingredient2')
        payload = {
            'name': ingredient['name']
        }
        res = self.client.put(ingredient_detail_url(
            slug=ingredient2['slug']), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_ingredient_success(self) -> None:
        ingredient = self._create_ingredient()
        res = self.client.delete(ingredient_detail_url(ingredient['slug']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_adding_tags_to_ingredient_success(self) -> None:
        ingredient = self._create_ingredient()
        tag = self._create_tag()
        payload = {
            'tag_ids': [tag['id'], ]
        }
        res = self.client.post(
            ingredient_tags_url(ingredient['slug']), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_mapping_unit_to_ingredient_success(self) -> None:
        ingredient = self._create_ingredient()
        unit = Unit.objects.create(name='test')
        payload = {
            'unit': unit.id,
            'grams': 100
        }
        res = self.client.post(
            ingredient_units_url(ingredient['slug']), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(unit.ingredient_set.all()[0].name, ingredient['name'])
