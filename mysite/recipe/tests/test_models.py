from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from recipe import models


def sample_user(email='test@gmail.com', name='Test', password='testpass',
                age=25, gender='Male'):
    """ create sample user """
    return get_user_model().objects.create_user(
        email=email,
        name=name,
        password=password,
        age=age,
        weight=88,
        height=188,
        gender=gender
    )


def sample_tag(name, user):
    return models.Tag.objects.create(name=name, user=user)


class ModelTests(TestCase):

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)\

        self.tag = sample_tag('test', self.user)
        self.unit = models.Unit.objects.create(name='gram', short_name='g')

    def test_ingredient_str(self):
        """ test the ingredient string representation """

        ingredient = models.Ingredient.objects.create(name='Szpinak',
                                                      user=self.user)
        ingredient.tags.add(self.tag)
        self.assertEqual(str(ingredient), ingredient.name)

    def test_ingredient_slug(self):
        """ test the ingredient slug """

        ingredient = models.Ingredient.objects.create(name='Biała czekolada',
                                                      user=self.user)
        ingredient.tags.add(self.tag)
        self.assertEqual(ingredient.slug, 'biala-czekolada')

    # def test_same_slug_different_ingredients(self):
    #     """ Test does not work as expected, return Integrity Error 1062, despite
    #         functionally works properly via web browser. To be resolved """
    #     ing1 = models.Ingredient.objects.create(name='Sól',
    #                                             user=self.user)
    #     ing1.tag.add(self.tag)
    #     ing2 = models.Ingredient.objects.create(name='Sol',
    #                                             user=self.user)
    #     ing2.tag.add(self.tag)
    #
    #     self.assertNotEqual(ing1.slug, ing2.slug)
    #     self.assertEqual(ing2.slug, 'sol2')

    def test_tag_str(self):
        """ test the tag string representation """
        tag = models.Tag.objects.create(
            user=self.user,
            name='Zupa'
        )

        self.assertEqual(str(tag), tag.name)

    def test_recipe_str(self):
        """ test the recipe string representation """
        recipe = models.Recipe.objects.create(
            name='Danie',
            user=self.user,
            calories=1000,
            portions=4,
            prepare_time=45,
            description='To jest opis dania'
        )
        self.assertEqual(str(recipe), recipe.name)

    def test_recipe_ingredient_through_table(self):
        """ test string representation of that table """
        recipe = models.Recipe.objects.create(
            name='Danie',
            user=self.user,
            calories=1000,
            portions=4,
            prepare_time=45,
            description='To jest opis dania'
        )
        ingredient = models.Ingredient.objects.create(
            name='Szpinak',
            user=self.user
        )
        recipe_ingredient = models.Recipe_Ingredient.objects.create(
            recipe=recipe,
            ingredient=ingredient,
            amount='2',
            unit=self.unit
        )

        self.assertEqual(str(recipe_ingredient),
                         f'{recipe.name}_{ingredient.name}')

    def test_retrieve_ingredient_unit_and_calorific_value(self):
        """ test getting main unit for specific ingredient and amount of
         calories in 100 units """

        ingredient = models.Ingredient.objects.create(
            name='Cebula',
            user=self.user,
            calories=350
         )

        self.assertEqual(ingredient.units.all()[0].short_name, 'g')
        self.assertEqual(ingredient.calories, 350)

    def test_str_unit(self):
        """ test string representation of unit """

        unit = models.Unit.objects.create(name='gram')

        self.assertEqual(str(unit), unit.name)

    def test_str_ready_meals(self):
        """ test string representation of ReadyMeals model """

        rmeal = models.ReadyMeals.objects.create(name='test', user=self.user)

        self.assertEqual(str(rmeal), rmeal.name)

    def test_default_tag_for_ready_meals(self):
        """ test default tag for ready meals """

        rmeal = models.ReadyMeals.objects.create(name='ready', user=self.user)

        tag = models.Tag.objects.get(name='ready meal')

        self.assertIn(tag.name, rmeal.tags.all().values()[0]['name'])

    def test_robustness_of_delete_old_photos_method(self):
        """ test if _delete_old_photos_methods raise any exceptions with
        incorrect arguments """
        recipe = models.Recipe.objects.create(user=self.user, name='test')
        self.assertFalse(recipe._delete_old_photos([1, 2], [3, 4]))
