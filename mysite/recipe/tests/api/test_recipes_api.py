from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from django.utils.text import slugify

from rest_framework.test import force_authenticate
from rest_framework.test import APIClient
from rest_framework import status

RECIPE_CREATE = reverse('recipe:recipe-create')


def recipe_detail_url(slug: str) -> str:
    return reverse('recipe:recipe-detail', kwargs={'slug': slug})


def recipe_tags_url(slug: str) -> str:
    return reverse('recipe:recipe-tags', kwargs={'slug': slug})


def recipe_ingredients_url(slug: str) -> str:
    return reverse('recipe:recipe-ingredients', kwargs={'slug': slug})


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
        payload = {
            'tag_ids': [1, 2, 3]
        }
        with patch('recipe.selectors.tag_ids_list') as mock:
            mock.return_value = [1, 2, 3]
            res = self.client.post(recipe_tags_url(recipe_slug), payload)
            self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_adding_non_existing_tags_to_recipe_failed(self) -> None:
        recipe_slug = self._create_recipe()
        payload = {
            'tag_ids': [1, 2, 3]
        }
        res = self.client.post(recipe_tags_url(recipe_slug), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_adding_ingredient_to_recipe_success(self) -> None:
    #     recipe_slug = self._create_recipe()
    #     payload = {[
    #         {
    #             'ingredient': 1,
    #             'amount': 100,
    #             'unit': 1,
    #         },
    #         {
    #             'ingredient': 2,
    #             'amount': 2,
    #             'unit': 3,
    #         }]}
    #     res = self.client.post(recipe_ingredients_url(recipe_slug), payload)
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
