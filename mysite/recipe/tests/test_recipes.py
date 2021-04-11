from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from recipe import models
from recipe.serializers import RecipeSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    """ create and return a sample recipe """
    defaults = {
        'name': 'Danie testowe',
        'calories': 1000,
        'prepare_time': 50,
        'portions': 4,
        'description': "Opis dania testowego"
    }
    defaults.update(params)

    return models.Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """ test unauthenticated recipe API access """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """ test that authentication is required """
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """ test authenticated recipe API Aaccess """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='testuser',
            password='testpass',
            age=25,
            sex='Male'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """ test retrieving a list of recipes """
        sample_recipe(self.user)
        params = {
            'name': 'test'
        }
        sample_recipe(self.user, **params)

        res = self.client.get(RECIPE_URL)

        recipes = models.Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """ test retrieving recipes for user """
        user2 = get_user_model().objects.create_user(
            email='test2@gmail.com',
            name='nazwa',
            password='testpass',
            age=25,
            sex='Male'
        )
        sample_recipe(user2)
        sample_recipe(self.user)

        res = self.client.get(RECIPE_URL)

        recipes = models.Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)
