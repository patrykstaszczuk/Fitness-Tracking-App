from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify

from rest_framework.test import force_authenticate
from rest_framework.test import APIClient
from rest_framework import status

from recipe.models import Recipe, Tag


def recipe_detail_url(slug: str) -> str:
    """ generate recipe detail url """
    return reverse('recipe:recipe-detail', kwargs={'slug': slug})


def group_recipe_detail_url(user: get_user_model, slug: str) -> str:
    """ generate group recipe detail url """
    return reverse('recipe:group-recipe-detail',
                   kwargs={'slug': slug, 'pk': user.id})


RECIPES_LIST = reverse('recipe:recipe-list')
RECIPE_CREATE = reverse('recipe:recipe-create')


def sample_recipe(user: get_user_model, name: str, portions=4, **params: dict):
    """ create sample recipe """
    slug = slugify(name)
    return Recipe.objects.create(user=user, name=name, slug=slug, portions=portions, ** params)


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


def sample_tag(user: get_user_model, name: str) -> Tag:
    """ create sample tag """
    slug = slugify(name)
    return Tag.objects.create(user=user, name=name, slug=slug)


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

    def test_get_recipes_by_unauth_user_failed(self):
        unauth_client = APIClient()
        res = unauth_client.get(RECIPES_LIST)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_recipes_success(self):
        user2 = sample_user('user2@gmail.com', 'user2')
        sample_recipe(user=self.auth_user, name='first recipe')
        sample_recipe(user=user2, name='second recipe')
        res = self.client.get(RECIPES_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_get_recipes_only_for_request_user(self):
        user2 = sample_user('user2@gmail.com', 'user2')
        sample_recipe(user=self.auth_user, name='first recipe')
        sample_recipe(user=user2, name='test')
        res = self.client.get(RECIPES_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_get_recipes_also_for_other_user_in_group(self):
        user2 = sample_user('user2@gmail.com', 'user2')
        user2_group = user2.own_group
        user2_group.members.add(self.auth_user)
        sample_recipe(user=self.auth_user, name='first recipe')
        sample_recipe(user=user2, name='user2 recipe')
        res = self.client.get(RECIPES_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_filtering_recipes_by_tags(self):
        recipe1 = sample_recipe(user=self.auth_user, name='test')
        recipe2 = sample_recipe(user=self.auth_user, name='test2')
        sample_recipe(user=self.auth_user, name='test3')
        tag1 = sample_tag(user=self.auth_user, name='tag1')
        tag2 = sample_tag(user=self.auth_user, name='tag2')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        res = self.client.get(
            RECIPES_LIST, {'tags': f'{tag1.slug},{tag2.slug}'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_filtering_recipes_by_invalida_tags(self):
        user2 = sample_user('2@gmail.com', 'name')
        recipe1 = sample_recipe(user=self.auth_user, name='test')
        tag1 = sample_tag(user=self.auth_user, name='tag1')
        tag2 = sample_tag(user=user2, name='tag2')
        recipe1.tags.add(tag1)

        res = self.client.get(
            RECIPES_LIST, {'tags': f'{tag1.slug},{tag2.slug}'})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_filtering_recipes_by_groups(self):
        user2 = sample_user('2@gmail.com', 'user2')
        user2_group = user2.own_group
        user2_group.members.add(self.auth_user)

        recipe1 = sample_recipe(user=self.auth_user, name='user1 recipe')
        recipe2 = sample_recipe(user=user2, name='user2 recipe')

        res = self.client.get(RECIPES_LIST, {'groups': f'{user2_group.id}'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_filtering_recipes_by_invalid_groups(self):
        user2 = sample_user('2@gmail.com', 'user2')
        user2_group = user2.own_group
        recipe1 = sample_recipe(user=self.auth_user, name='user1 recipe')
        recipe2 = sample_recipe(user=user2, name='user2 recipe')

        res = self.client.get(RECIPES_LIST, {'groups': f'{user2_group.id}'})
        print(res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_recipe_detail_success(self):
        recipe = sample_recipe(user=self.auth_user, name='recipe')
        res = self.client.get(recipe_detail_url(recipe.slug))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], recipe.id)

    def test_get_other_user_recipe_detail_not_found_if_not_in_group(self):
        user2 = sample_user('user2@gmail.com', 'user2')
        recipe = sample_recipe(user=user2, name='recipe')
        res = self.client.get(recipe_detail_url(recipe.slug))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_other_user_recipe_detail_in_common_group_success(self):
        user2 = sample_user('user2@gmail.com', 'user2')
        recipe = sample_recipe(user=user2, name='recipe')

        user2_group = user2.own_group
        user2_group.members.add(self.auth_user)

        res = self.client.get(group_recipe_detail_url(
            user=user2, slug=recipe.slug))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], recipe.id)

    def test_create_recipe_success(self):
        tag = sample_tag(user=self.auth_user, name='test')
        payload = {
            'name': 'recipe',
            'portions': 3,
            'tags': [tag.slug, ]
        }
        res = self.client.post(RECIPE_CREATE, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('location', res._headers)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(len(res.data['tags']), 1)

    def test_create_recipe_with_two_tags_success(self):
        tag1 = sample_tag(user=self.auth_user, name='tag1')
        tag2 = sample_tag(user=self.auth_user, name='tag2')
        payload = {
            'name': 'recipe',
            'portions': 3,
            'tags': [tag1.slug, tag2.slug]
        }
        res = self.client.post(RECIPE_CREATE, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('location', res._headers)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(len(res.data['tags']), 2)

    def test_create_recipe_without_tag_failed(self):
        payload = {
            'name': 'teest',
            'portions': 3
        }
        res = self.client.post(RECIPE_CREATE, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_non_existing_tag_failed(self):
        payload = {
            'name': 'teest',
            'portions': 3,
            'tags': ['str']
        }
        res = self.client.post(RECIPE_CREATE, payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_recipe_with_other_user_tag_failed(self):
        user2 = sample_user(email='test2@gmail.com', name='test')
        tag = sample_tag(user=user2, name='test')

        payload = {
            'name': 'teest',
            'portions': 3,
            'tags': [tag.slug]
        }
        res = self.client.post(RECIPE_CREATE, payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_recipe_repeated_name_failed(self):
        sample_recipe(user=self.auth_user, name='test')
        tag = sample_tag(user=self.auth_user, name='tag')
        payload = {
            'name': 'test',
            'tags': [tag.slug, ]
        }
        res = self.client.post(RECIPE_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_ingredients(self):
        pass
