from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify

from rest_framework.test import APIClient
from rest_framework import status

from recipe.models import Ingredient, Tag, Unit


INGREDIENT_LIST = reverse('recipe:ingredient-list')
INGREDIENT_CREATE = reverse('recipe:ingredient-create')


def ingredient_detail_url(slug: str) -> str:
    """ generate url for ingredient detail endpoint """
    return reverse('recipe:ingredient-detail', kwargs={'slug': slug})


def ingredient_update_url(slug: str) -> str:
    """ generate url for ingredient update endpoint """
    return reverse('recipe:ingredient-update', kwargs={'slug': slug})


def ingredient_delete_url(slug: str) -> str:
    """ generate url for ingredient delete endpoint """
    return reverse('recipe:ingredient-delete', kwargs={'slug': slug})


def sample_ingredient(user: get_user_model, name: str, **kwargs):
    """ create a sample ingredient with simple slug """
    slug = slugify(name)
    return Ingredient.objects.create(user=user, name=name, slug=slug, **kwargs)


def sample_tag(user: get_user_model, name: str) -> Tag:
    """ create sampel tag """
    slug = slugify(name)
    return Tag.objects.create(user=user, name=name, slug=slug)


def sample_user(email: str, name: str) -> get_user_model:
    """ create sample user """
    return get_user_model().objects.create_user(
        email=email,
        name=name,
        password='authpass',
        gender='M',
        age=25,
        height=188,
        weight=73,
    )


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

    def test_retrieve_ingredient_by_unauth_user_forbidden(self):
        unauth_user = APIClient()
        res = unauth_user.get(INGREDIENT_LIST)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_ingredients_succcess(self):
        sample_ingredient(user=self.auth_user, name='test')
        sample_ingredient(user=self.auth_user, name='test2')

        res = self.client.get(INGREDIENT_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_retrieving_tags_names_in_ingredients_list(self):
        ing = sample_ingredient(user=self.auth_user, name='test')
        tag = Tag.objects.create(user=self.auth_user, name='tag')
        ing.tags.add(tag)

        res = self.client.get(INGREDIENT_LIST)
        self.assertEqual(res.data[0]['tags'][0], tag.name)

    def test_retreive_ingredient_detail(self):
        ing = sample_ingredient(user=self.auth_user, name='test')

        res = self.client.get(ingredient_detail_url(ing.slug))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], ing.id)

    def test_retreive_other_user_ingredient_detail(self):
        user2 = sample_user(email='test@gmail.com', name='test')
        ing = sample_ingredient(user=user2, name='test')

        res = self.client.get(ingredient_detail_url(ing.slug))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], ing.id)

    def test_retreiving_units_information_in_ingredient_detail(self):
        unit = Unit.objects.create(name='gram')
        ing = sample_ingredient(user=self.auth_user, name='ing')
        ing.units.add(unit, through_defaults={'grams_in_one_unit': 100})

        res = self.client.get(ingredient_detail_url(ing.slug))
        self.assertEqual(unit.id, res.data['units'][0]['id'])

    def test_create_ingredient(self):

        payload = {
            'name': 'test',
        }
        res = self.client.post(INGREDIENT_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('location', res._headers)

    def test_create_ingredient_with_tags(self):
        tag1 = sample_tag(self.auth_user, 'tag1')
        tag2 = sample_tag(self.auth_user, 'tag2')

        payload = {
            'name': 'test',
            'tags': [tag1.slug, tag2.slug]
        }
        res = self.client.post(INGREDIENT_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]

        res = self.client.get(url)
        self.assertEqual(len(res.data['tags']), 2)

    def test_create_ingredient_with_extra_units(self):
        unit = Unit.objects.create(name='new')

        payload = {
            'name': 'test',
            'units': [{'unit': unit.id, 'grams_in_one_unit': 20}]
        }
        res = self.client.post(INGREDIENT_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        res = self.client.get(res._headers['location'][1])
        self.assertEqual(len(res.data['units']), 2)

    def test_create_ready_meal(self):
        payload = {
            'ready_meal': True,
            'name': 'test'
        }
        res = self.client.post(INGREDIENT_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        res = self.client.get(res._headers['location'][1])
        self.assertEqual(res.data['tags'][0]['slug'], 'ready-meal')

    def test_create_ready_meal_with_invalid_tag(self):
        payload = {
            'ready_meal': 'string insted of bool',
            'name': 'test'
        }
        res = self.client.post(INGREDIENT_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ingredient_missing_required_field(self):
        payload = {
            'calories': 100
        }
        res = self.client.post(INGREDIENT_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ingredient_repeated_name(self):
        sample_ingredient(user=self.auth_user, name='test')
        payload = {
            'name': 'test',
        }
        res = self.client.post(INGREDIENT_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ingredient_with_invalid_fields(self):
        payload = {
            'name': 'test',
            'calories': -200
        }
        res = self.client.post(INGREDIENT_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ingredient_same_name_but_different_user(self):
        user2 = sample_user('2@gmail.com', '2')
        sample_ingredient(user2, 'test')
        payload = {
            'name': 'test',
        }
        res = self.client.post(INGREDIENT_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_update_ingredient_success(self):
        ing = sample_ingredient(user=self.auth_user, name='test')
        payload = {
            'name': 'new name'
        }
        res = self.client.put(ingredient_update_url(
            ing.slug), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = res._headers.get('location')[1]
        res = self.client.get(url)
        self.assertEqual(res.data['name'], payload['name'])
        self.assertNotEqual(res.data['slug'], ing.slug)

    def test_update_ingredients_tags_with_put(self):
        tag = sample_tag(self.auth_user, 'tag name')
        ing = sample_ingredient(user=self.auth_user, name='test')
        ing.tags.add(tag)

        new_tag = sample_tag(self.auth_user, 'new tag')
        payload = {
            'tags': [new_tag.slug, ]
        }
        res = self.client.put(ingredient_update_url(
            ing.slug), payload, format='json')
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(len(res.data['tags']), 1)
        self.assertEqual(res.data['tags'][0]['name'], new_tag.name)

    def test_update_ingredients_tags_with_patch(self):
        tag = sample_tag(self.auth_user, 'tag name')
        ing = sample_ingredient(user=self.auth_user, name='test')
        ing.tags.add(tag)

        new_tag = sample_tag(self.auth_user, 'new tag')
        payload = {
            'tags': [new_tag.slug, ]
        }
        res = self.client.patch(ingredient_update_url(
            ing.slug), payload, format='json')
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(len(res.data['tags']), 2)
        self.assertEqual(res.data['tags'][0]['name'], tag.name)
        self.assertEqual(res.data['tags'][1]['name'], new_tag.name)

    def test_update_other_user_ingredient_failed(self):
        user2 = sample_user('2@gmail.com', 'test')
        ing = sample_ingredient(user=user2, name='test')
        res = self.client.put(ingredient_update_url(ing.slug))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_ingredient(self):
        ing = sample_ingredient(user=self.auth_user, name='test')
        res = self.client.delete(ingredient_delete_url(ing.slug))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ings = Ingredient.objects.filter(user=self.auth_user)
        self.assertEqual(len(ings), 0)

    def test_delete_other_user_ingredient_failed(self):
        user2 = sample_user('2@gmail.com', 'test')
        ing = sample_ingredient(user=user2, name='test')
        res = self.client.delete(ingredient_delete_url(ing.slug))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        ings = Ingredient.objects.filter(user=user2)
        self.assertEqual(len(ings), 1)
