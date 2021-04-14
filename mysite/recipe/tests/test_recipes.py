from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from recipe import models
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_slug):
    """ return recile detail URL """
    return reverse('recipe:recipe-detail', args=[recipe_slug])


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


def sample_tag(user, name):
    """ create and return sampel tag """
    return models.Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name):
    """ create sample ingredeint """
    return models.Ingredient.objects.create(user=user, name=name)


class PublicRecipeApiTests(TestCase):
    """ test unauthenticated recipe API access """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """ test that authentication is required """
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(APITestCase):
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

    def test_view_recipe_detail(self):
        """ test viewing a recipe detail """
        recipe = sample_recipe(user=self.user)
        recipe.tag.add(sample_tag(self.user, 'vege'))
        recipe.ingredient.add(sample_ingredient(self.user, 'szpinak'))

        url = detail_url(recipe.slug)

        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """ test creating recipe """
        payload = {
            'name': 'Hamburgery vege',
            'description': 'opis dania'
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = models.Recipe.objects.get(id=res.data['id'])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """ test creating a recipe with tags """
        tag1 = sample_tag(user=self.user, name='Vege')
        tag2 = sample_tag(user=self.user, name='Deser')
        payload = {
            'name': 'placki z czekolada',
            'tag': [tag1, tag2],
            'description': "opis dania"
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = models.Recipe.objects.get(id=res.data['id'])
        tags = recipe.tag.all()

        self.assertEqual(len(tags), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """ test creating recipe with ingredients """
        ingredient1 = sample_ingredient(user=self.user, name='Krewetki')
        ingredient2 = sample_ingredient(user=self.user, name='Masło')
        tag = sample_tag(user=self.user, name='Deser')
        payload = {
            'name': 'dobry obiad',
            'tags': [tag.id, ],
            "ingredients": [{
                "ingredient": ingredient1.id,
                "quantity": "2kg"
            }, {
                "ingredient": ingredient2.id,
                "quantity": "2kg"
            }, ],
            'description': "opis dania",
            'test': 'cos',
            # 'test_1': '1',
            # 'test_2': '2',
        }
        res = self.client.post(RECIPE_URL, payload, format='json')
        #print(res.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = models.Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(len(ingredients), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)
