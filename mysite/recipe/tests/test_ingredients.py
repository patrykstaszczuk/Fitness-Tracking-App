from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from recipe import models
from recipe.serializers import IngredientSerializer, UnitSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')
UNITS = reverse('recipe:units')


def reverse_ingredient_detail(slug):
    return reverse('recipe:ingredient-detail', kwargs={'slug': slug})


def sample_ingredient(**kwargs):
    return models.Ingredient.objects.create(**kwargs)


def sample_tag(name, user):
    return models.Tag.objects.create(name=name, user=user)


def sample_user(email='user2@gmail.com', name='test2'):
    return get_user_model().objects.create_user(
        email=email,
        name=name,
        password='testpass',
        age=25,
        weight=88,
        height=188,
        sex='Male'
    )


class PublicIngredientApiTests(TestCase):
    """ test the publicly available ingredients API """

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """ test that login is required to access ingredients API """
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """ test the private ingredient API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='testpass',
            name='Test',
            age=25,
            weight=88,
            height=188,
            sex='Male'
        )
        self.tag = sample_tag('test', self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.unit = models.Unit.objects.create(name='gram')

    def test_retrieve_ingredients(self):
        """ test retrieving ingredients tags """

        sample_ingredient(name="czosnek", user=self.user)
        sample_ingredient(name="szpinak", user=self.user)

        res = self.client.get(INGREDIENTS_URL)
        ingredients = models.Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertTrue(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """ test that ingredients returned are for specific user """
        user2 = sample_user()
        ingredient = sample_ingredient(name='Szpinak', user=self.user)
        sample_ingredient(name='Czosnek', user=user2)

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_retrieve_calories_from_ingredient(self):
        """ test getting amount of calories in 100g of ingredient """

        ingredient = sample_ingredient(
            user=self.user,
            name='Cukinia',
            calories=17)

        res = self.client.get(reverse_ingredient_detail(ingredient.slug))

        serializer = IngredientSerializer(ingredient)

        self.assertEqual(res.data, serializer.data)

    def test_retrieve_nutritional_value_of_ingredient(self):
        """ test getting nutrional value from ingredient """

        ingredient = sample_ingredient(
            name='Cukinia',
            user=self.user,
            carbohydrates=3,
            fats=0,
            proteins=1,
            fiber=1,
            sodium=8,
            potassium=261,
            calcium=16,
            iron=0.37,
            magnesium=18,
            selenium=0.2,
            zinc=0.32,
        )

        res = self.client.get(reverse_ingredient_detail(ingredient.slug))

        serializer = IngredientSerializer(ingredient)

        self.assertEqual(res.data, serializer.data)

    def test_create_ingredient_sucessful(self):
        """ test creating new ingredient """
        payload = {
            'name': 'Cebula',
            'tags': self.tag.slug
        }
        res = self.client.post(INGREDIENTS_URL, payload)
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
        sample_ingredient(name='Majonez', user=self.user)

        payload = {
            'name': 'Majonez',
            'user': self.user.id,
        }
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ingredient_with_invalid_calories_filed(self):
        """ test creating new ingredient with negative value of calories """

        payload = {
            'name': 'Cukinia',
            'calories': -1,
        }

        res = self.client.post(INGREDIENTS_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ingredient_success_different_user(self):
        """ test create ingredient success with same name but different user"""
        user2 = sample_user()
        sample_ingredient(name='Majonez', user=user2)

        payload = {
            'name': 'Majonez',
            'user': self.user,
            'tags': self.tag.slug
        }

        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        ingredients = models.Ingredient.objects.filter(user=user2) \
            .filter(name=payload['name'])

        self.assertEqual(len(ingredients), 1)

    def test_delete_ingredient_success(self):
        """ test deleting ingredient with success """
        ingredient = sample_ingredient(name='Majonez', user=self.user)
        res = self.client.delete(reverse_ingredient_detail(ingredient.slug))
        ingredient = models.Ingredient.objects.filter(user=self.user). \
            filter(name=ingredient.name).exists()

        self.assertFalse(ingredient)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_full_update_ingredient_success(self):
        """ test update ingredient with success """
        ingredient = sample_ingredient(name='Majonez', user=self.user)
        payload = {
            'name': 'Mąka',
            'tags': self.tag.slug
        }
        res = self.client.put(reverse_ingredient_detail(ingredient.slug), payload)
        ingredient = models.Ingredient.objects.filter(id=ingredient.id)[0]

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.name, payload['name'])

    def test_partial_ingredient_update_success(self):
        """ test that partial ingredient update works """
        ingredient = sample_ingredient(name='Majonez', user=self.user)
        payload = {
            'tags': self.tag.slug
        }
        res = self.client.patch(reverse_ingredient_detail(ingredient.slug),
                                                           payload)

        ingredient = models.Ingredient.objects.filter(id=ingredient.id)[0]
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.tags.first(), self.tag)

    def test_full_ingredient_update_same_name(self):
        """ test full ingredient update with the same name """
        ingredient = sample_ingredient(name='Majonez', user=self.user)
        payload = {
            'name': 'Majonez',
            'tags': self.tag.slug
        }
        res = self.client.put(reverse_ingredient_detail(ingredient.slug), payload)
        ingredient = models.Ingredient.objects.filter(id=ingredient.id)[0]

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.tags.first(), self.tag)

    def test_available_units(self):
        """ test retrieving available units """

        models.Unit.objects.create(name='gram', short_name='g')
        models.Unit.objects.create(name='mililitry', short_name='ml')
        models.Unit.objects.create(name='sztuk', short_name='sztuk')
        models.Unit.objects.create(name='szklanka', short_name='szklanka')

        res = self.client.get(UNITS)

        all_units = models.Unit.objects.all()

        serializer = UnitSerializer(all_units, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_retrieve_default_unit_for_ingredient(self):
        """ test retrieving all units set to ingredient """

        ing = sample_ingredient(user=self.user, name='Cukinia')

        res = self.client.get(reverse_ingredient_detail(ing.slug))

        unit = models.Unit.objects.get(name='gram')
        serializer = UnitSerializer(unit)

        self.assertEqual(res.json()['available_units'][0], serializer.data)

    def test_retrieve_available_units_for_ingredient(self):
        """ test retrieving all units set to ingredient """

        ing = sample_ingredient(user=self.user, name='Cukier')
        spoon = models.Unit.objects.create(name='spoon', short_name='sp')
        pinch = models.Unit.objects.create(name='pinch', short_name='pn')
        ing.units.add(spoon, through_defaults={'grams_in_one_unit': 5})

        res = self.client.get(reverse_ingredient_detail(ing.slug))
        print(res.data)
        all_units = models.Unit.objects.filter(name__in=['gram', 'spoon'])
        serializer = UnitSerializer(all_units, many=True)
        self.assertEqual(res.json()['available_units'], serializer.data)

    def test_create_ingredient_unit_mapping(self):
        """ test creating mapping for new ingredient """

        ing = sample_ingredient(user=self.user, name='Cukinia')
        spoon = models.Unit.objects.create(name='spoon', short_name='sp')
        payload = {
            'unit': spoon.id,
            'grams_in_one_unit': 50
        }

    # @patch('uuid.uuid4')
    # def test_recipe_file_name_uuid(self, mock_uuid):
    #     """ test that image is saved in the correct location """
    #     uuid = 'test-uuid'
    #     mock_uuid.return_value = uuid
    #     file_path = models.recipe_image_file_path(self.sample_recipe,
    #                                               'myimage.jpg')
    #
    #     exp_path = f'recipes/{self.user.name}/{self.sample_recipe.slug}/{uuid}.jpg'
    #     self.assertEqual(file_path, exp_path)
