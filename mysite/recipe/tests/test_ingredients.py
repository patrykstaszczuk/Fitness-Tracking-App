from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.reverse import reverse as rest_reverse

from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status

from recipe import models
from recipe.serializers import IngredientSerializer, UnitSerializer,  \
    IngredientUnitSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')
UNITS = reverse('recipe:units')


def ingredient_detail_url(slug):
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
        gender='Male'
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
            gender='Male'
        )
        self.tag = sample_tag('test', self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.unit = models.Unit.objects.create(name='gram')
        self.request = APIRequestFactory().get('/')

    def test_retrieve_ingredients(self):
        """ test retrieving ingredients tags """

        ing1 = sample_ingredient(name="czosnek", user=self.user)
        ing2 = sample_ingredient(name="szpinak", user=self.user)

        res = self.client.get(INGREDIENTS_URL)
        ingredients = models.Ingredient.objects.all().order_by('-name')

        self.assertTrue(res.status_code, status.HTTP_200_OK)
        self.assertIn(ing1.name, res.json()['data'][0]['name'])
        self.assertIn(ing2.name, res.json()['data'][1]['name'])
    #
    # def test_ingredient_limited_to_user(self):
    #     """ test that ingredients returned are for specific user """
    #     user2 = sample_user()
    #     ingredient = sample_ingredient(name='Szpinak', user=self.user)
    #     sample_ingredient(name='Czosnek', user=user2)
    #
    #     res = self.client.get(INGREDIENTS_URL)
    #
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     self.assertEqual(len(res.data), 1)
    #     self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_retreiving_ingredient_detail(self):
        """ test retrieving ingredient detail where multi users created
        ingredient with the same name """

        user2 = sample_user()
        user2_ing = sample_ingredient(user=user2, name='test')
        self_user_ing = sample_ingredient(user=self.user, name='test')

        res = self.client.get(ingredient_detail_url(self_user_ing.slug))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieving_other_user_ingredient_detail(self):
        """ test retrieving ingredient detail created by other user """
        user2 = sample_user()
        user2_ing = sample_ingredient(user=user2, name='test', calories='1000')
        self_user_ing = sample_ingredient(user=self.user, name='test',
                                          calories='900')

        payload = {
            'user': user2.id
        }
        res = self.client.get(ingredient_detail_url(user2_ing.slug), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['data']['calories'],
                         float(user2_ing.calories))

    def test_retrieving_proper_url_for_other_user_ingredient(self):
        """ test that url returned by serializer is user tag in GET
        query params """
        print("\n\n\n")
        print("self.queryset != Ingredient.objects.alll() ???? ")
        user2 = sample_user()
        user2_ing = sample_ingredient(user=user2, name='test',
                                      calories='1000')
        res = self.client.get(INGREDIENTS_URL)
        url = rest_reverse('recipe:ingredient-detail', kwargs={'slug': user2_ing.slug}, request=self.request)
        url = url + f'?user={user2.id}'
        self.assertEqual(res.json()['data'][0]['url'], str(url))

    def test_retrieve_calories_from_ingredient(self):
        """ test getting amount of calories in 100g of ingredient """

        ingredient = sample_ingredient(
            user=self.user,
            name='Cukinia',
            calories=17)

        res = self.client.get(ingredient_detail_url(ingredient.slug))
        self.assertEqual(res.json()['data']['calories'], ingredient.calories)

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

        res = self.client.get(ingredient_detail_url(ingredient.slug))
        self.assertIn(ingredient.name, res.json()['data']['name'])

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

    def test_create_read_meal_successful(self):
        """ test crete ready meal successfull """

        payload = {
            'ready_meal': True,
            'name': 'Pizza',
            'calories': 350,
            'proteins': 43,
            'carbohydrates': 60,
            'fats': 20
        }
        res = self.client.post(INGREDIENTS_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        rmeal = models.ReadyMeals.objects.get(name=payload['name'])
        self.assertEqual('Ready Meal', rmeal.tags.all()[0].name)

    def test_create_ready_meal_with_invalid_flag(self):
        """ test creating ready meal but with invalid ready meal flag """

        payload = {
            'ready_meal': "String insted of bool",
            'name': 'Pizza',
            'calories': 350,
            'proteins': 43,
            'carbohydrates': 60,
            'fats': 20
        }
        res = self.client.post(INGREDIENTS_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        rmeal = models.ReadyMeals.objects.get(name=payload['name'])
        self.assertEqual(len(rmeal.tags.all()), 0)

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
        res = self.client.delete(ingredient_detail_url(ingredient.slug))
        ingredient = models.Ingredient.objects.filter(user=self.user). \
            filter(name=ingredient.name).exists()

        self.assertFalse(ingredient)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_user_ingredient_failed(self):
        """ test deleting other user ingredient failed """
        user2 = sample_user()
        user2_ing = sample_ingredient(user=user2, name='test')
        payload = {
            "user": user2.id
        }
        res = self.client.delete(ingredient_detail_url(user2_ing.slug), payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_full_update_ingredient_success(self):
        """ test update ingredient with success """
        ingredient = sample_ingredient(name='Majonez', user=self.user)
        payload = {
            'name': 'Mąka',
            'tags': self.tag.slug
        }
        res = self.client.put(ingredient_detail_url(ingredient.slug), payload)
        ingredient = models.Ingredient.objects.filter(id=ingredient.id)[0]

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.name, payload['name'])

    def test_update_other_user_ingredient_failed(self):
        """ test updating other user ingredient failed as not found """
        user2 = sample_user()
        user2_ing = sample_ingredient(user=user2, name='test')
        payload = {
            "name": 'test2'
        }
        res = self.client.put(ingredient_detail_url(user2_ing.slug), payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_ingredient_update_success(self):
        """ test that partial ingredient update works """
        ingredient = sample_ingredient(name='Majonez', user=self.user)
        payload = {
            'tags': self.tag.slug
        }
        res = self.client.patch(ingredient_detail_url(ingredient.slug),
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
        res = self.client.put(ingredient_detail_url(ingredient.slug), payload)
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

        serializer = UnitSerializer(all_units, many=True, context={'request': self.request})

        self.assertEqual(res.data, serializer.data)

    def test_retrieve_default_unit_for_ingredient(self):
        """ test retrieving all units set to ingredient """

        ing = sample_ingredient(user=self.user, name='Cukinia')

        res = self.client.get(ingredient_detail_url(ing.slug))

        self.assertEqual(res.json()['data']['available_units'][0]['unit'], self.unit.id)

    def test_retrieve_available_units_for_ingredient(self):
        """ test retrieving all units set to ingredient """

        ing = sample_ingredient(user=self.user, name='Cukier')
        spoon = models.Unit.objects.create(name='spoon', short_name='sp')
        pinch = models.Unit.objects.create(name='pinch', short_name='pn')
        ing.units.add(spoon, through_defaults={'grams_in_one_unit': 5})

        res = self.client.get(ingredient_detail_url(ing.slug))
        all_units = models.Ingredient_Unit.objects.filter(ingredient=ing)
        serializer = IngredientUnitSerializer(all_units, many=True, context={'request': self.request})
        self.assertEqual(res.json()['data']['available_units'], serializer.data)

    def test_create_ingredient_unit_mapping(self):
        """ test creating mapping for new ingredient """

        ing = sample_ingredient(user=self.user, name='Cukinia')
        spoon = models.Unit.objects.create(name='spoon', short_name='sp')
        payload = {
            'units': [{
                'unit': spoon.id,
                'grams_in_one_unit': 50
                }
            ]
        }

        res = self.client.patch(ingredient_detail_url(ing.slug), payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ing.refresh_from_db()
        self.assertEqual(len(ing.units.all()), 2)

    def test_create_ingredient_unit_mapping_failed_invalid_unit(self):
        """ test create unit mapping with invalid unit instance"""

        ing = sample_ingredient(user=self.user, name='Cukinia')

        payload = {
            'units': [{
                'unit': 99,
                'grams_in_one_unit': 100
            }]
        }
        res = self.client.patch(ingredient_detail_url(ing.slug), payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_ingredient_unit_mapping(self):
        """ test upgrade ingredient unit mapping """

        ing = sample_ingredient(user=self.user, name='Cukinia')
        unit = models.Unit.objects.create(name='spoon', short_name='sp')
        ing.units.add(unit, through_defaults={'grams_in_one_unit': 80})

        payload = {
            'units': [{
                'unit': unit.id,
                'grams_in_one_unit': 100
            }]
        }
        res = self.client.patch(ingredient_detail_url(ing.slug), payload,
                                format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['data']['available_units'][1]['grams_in_one_unit'],
                         100)
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
