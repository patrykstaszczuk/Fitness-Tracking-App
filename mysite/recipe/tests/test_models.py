from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from recipe import models


def sample_user(email='test@gmail.com', name='Test', password='testpass',
                age=25, sex='Male'):
    """ create sample user """
    return get_user_model().objects.create_user(
        email=email,
        name=name,
        password=password,
        age=age,
        sex=sex
    )


class PrivateRecipeApiTests(TestCase):

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)\


    def test_ingredient_str(self):
        """ test the ingredient string representation """

        ingredient = models.Ingredient.objects.create(name='Szpinak',
                                                      type='V',
                                                      user=self.user)
        self.assertEqual(str(ingredient), ingredient.name)

    def test_ingredient_slug(self):
        """ test the ingredient slug """

        ingredient = models.Ingredient.objects.create(name='Biała czekolada',
                                                      type='W',
                                                      user=self.user)
        self.assertEqual(ingredient.slug, 'biala-czekolada')

    def test_same_slug_different_ingredients(self):
        ing1 = models.Ingredient.objects.create(name='Sól', type='W',
                                                user=self.user)
        ing2 = models.Ingredient.objects.create(name='Sol', type='V',
                                                user=self.user)

        self.assertNotEqual(ing1.slug, ing2.slug)
        self.assertEqual(ing2.slug, 'sol2')

    def test_tag_str(self):
        """ test the tag string representation """
        tag = models.Tag.objects.create(
            user=self.user,
            name='Zupa'
        )

        self.assertEqual(str(tag), tag.name)
    # def test_recipe_str(self):
    #     """ test the recipe string representation """
    #     recipe = models.Recipe.objects.create(
    #         name='Danie',
    #         user=sample_user(),
    #         type='V',
    #         category='O'
    #     )
    #     self.assertEqual(str(recipe), recipe.name)
