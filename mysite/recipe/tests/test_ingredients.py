from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from recipe import models
from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def reverse_ingredient_detail(slug):
    return reverse('recipe:ingredient-detail', kwargs={'slug': slug})


def sample_ingredient(name, user):
    return models.Ingredient.objects.create(name=name, user=user)


def sample_tag(name, user):
    return models.Tag.objects.create(name=name, user=user)


class PublicIngredientApiTests(TestCase):
    """ test the publicly available ingredients API """

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """ test that login is required to access ingredients API """
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTest(TestCase):
    """ test the private ingredient API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='testpass',
            name='Test',
            age=25,
            sex='Male'
        )
        self.tag = sample_tag('test', self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        """ test retrieving ingredients tags """

        sample_ingredient("czosnek", self.user)
        sample_ingredient("szpinak", self.user)

        res = self.client.get(INGREDIENTS_URL)
        ingredients = models.Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertTrue(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """ test that ingredients returned are for specific user """
        user2 = get_user_model().objects.create_user(
            email='test2@gmail.com',
            password='testpass',
            name='Test',
            age=25,
            sex='Male'
        )
        ingredient = sample_ingredient('Szpinak', self.user)
        sample_ingredient('Czosnek', user2)

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_sucessful(self):
        """ test creating new ingredient """
        payload = {
            'name': 'Cebula',
            'tag': self.tag
        }
        self.client.post(INGREDIENTS_URL, payload)
        exists = models.Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """ test create ingredient with invalid payload """
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ingredient_repeated_name(self):
        """ test create ingredient which already is in database """
        sample_ingredient('Majonez', self.user)

        payload = {
            'name': 'Majonez',
            'user': self.user.id,
        }
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ingredient_success_different_user(self):
        """ test create ingredient success with same name but different user"""
        user2 = get_user_model().objects.create_user(
            email='Test3@gmail.com',
            password='password2',
            name='test',
            age=25,
            sex='Male'
        )
        sample_ingredient('Majonez', user2)

        payload = {
            'name': 'Majonez',
            'user': self.user,
            'tag': self.tag
        }

        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        ingredients = models.Ingredient.objects.filter(user=user2) \
            .filter(name=payload['name'])

        self.assertEqual(len(ingredients), 1)

    def test_delete_ingredient_success(self):
        """ test deleting ingredient with success """
        ingredient = sample_ingredient('Majonez', self.user)
        res = self.client.delete(reverse_ingredient_detail(ingredient.slug))
        ingredient = models.Ingredient.objects.filter(user=self.user). \
            filter(name=ingredient.name).exists()

        self.assertFalse(ingredient)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_full_update_ingredient_success(self):
        """ test update ingredient with success """
        ingredient = sample_ingredient('Majonez', self.user)
        payload = {
            'name': 'Mąka',
            'tag': self.tag
        }
        res = self.client.put(reverse_ingredient_detail(ingredient.slug), payload)
        ingredient = models.Ingredient.objects.filter(id=ingredient.id)[0]

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.name, payload['name'])

    def test_partial_ingredient_update_success(self):
        """ test that partial ingredient update works """
        ingredient = sample_ingredient('Majonez', self.user)
        payload = {
            'tag': self.tag
        }
        res = self.client.patch(reverse_ingredient_detail(ingredient.slug),
                                                           payload)
        ingredient = models.Ingredient.objects.filter(id=ingredient.id)[0]
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.tag.first(), self.tag)

    def test_full_ingredient_update_same_name(self):
        """ test full ingredient update with the same name """
        ingredient = sample_ingredient('Majonez', self.user)
        payload = {
            'name': 'Majonez',
            'tag': self.tag
        }
        res = self.client.put(reverse_ingredient_detail(ingredient.slug), payload)
        ingredient = models.Ingredient.objects.filter(id=ingredient.id)[0]

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.tag.first(), self.tag)
