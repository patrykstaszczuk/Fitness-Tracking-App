from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from recipe import models
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer, \
                                IngredientSerializer

from unittest.mock import patch

from users import models as user_models

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


def sample_user(email='user2@gmail.com', name='testusername'):
    return get_user_model().objects.create_user(
        email=email,
        name=name,
        password='testpass',
        age=25,
        sex='Male'
    )


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

        self.user_tag = sample_tag(self.user, 'Tag testowy')

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

    def test_view_group_recipes(self):
        """ test retrieving recipes created by user and other users in the
        same group """

        user2 = sample_user()
        user2_recipe = sample_recipe(user2)
        params = {
            'name': 'recipeuser2'
        }
        user3 = sample_user(email='test3@gmail.com', name='test3name')
        user3_recipe = sample_recipe(user3)

        user4 = sample_user(email='test4@gmail.com', name='test4name')
        user4_recipe = sample_recipe(user4)

        user2_recipe.tags.add(sample_tag(user2, 'vege'))
        user2_recipe.ingredients.add(sample_ingredient(user2, 'cukinia'))
        user3_recipe.tags.add(sample_tag(user3, 'vege'))
        user3_recipe.ingredients.add(sample_ingredient(user3, 'cukinia'))

        group_user2 = user_models.Group.objects.create(founder=user2)
        group_user3 = user_models.Group.objects.create(founder=user3)
        group_user4 = user_models.Group.objects.create(founder=user4)

        self.user.membership.add(group_user2, group_user3)

        recipe = sample_recipe(self.user, **params)
        res = self.client.get(RECIPE_URL)
        user2_recipe = models.Recipe.objects.get(user=user2)
        user3_recipe = models.Recipe.objects.get(user=user3)
        serializer_recipes = RecipeSerializer([user2_recipe, user3_recipe],
                                              many=True)
        serializer_recipe_user4 = RecipeSerializer([user4_recipe, ], many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_recipes.data[0], res.data)
        self.assertNotIn(serializer_recipe_user4.data, res.data)

    def test_view_recipe_detail(self):
        """ test viewing a recipe detail """
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(self.user, 'vege'))
        recipe.ingredients.add(sample_ingredient(self.user, 'szpinak'))

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
            'tags': [tag1.slug, tag2.slug],
            'ingredients': [],
            'description': "opis dania"
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = models.Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

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
            'tags': [tag.slug, ],
            "ingredients": [{
                "ingredient": ingredient1.slug,
                "quantity": "2kg"
            }, {
                "ingredient": ingredient2.slug,
                "quantity": "2kg"
            }, ],
            'description': "opis dania",
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = models.Recipe.objects.get(id=res.data['id'])

        recipe_ingredient = models.Recipe_Ingredient.objects.filter(
            recipe=recipe
        ).count()
        self.assertEqual(recipe_ingredient, 2)
        ingredients = recipe.ingredients.all()

        self.assertEqual(len(ingredients), 2)
        self.assertEqual(len(ingredients), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_create_multi_recipes_for_multi_users(self):
        """ create multi recipes for multi users """
        user2 = get_user_model().objects.create(
                email='test2@gmail.com',
                name='testuser2',
                password='testpass',
                age=25,
                sex='Male'
        )
        ingredient_self_user = sample_ingredient(self.user, 'Szpinak')
        ingredient_user2 = sample_ingredient(user2, 'Czonsek')

        tag_self_user = sample_tag(self.user, 'Vege')
        tag_user2 = sample_tag(user2, 'Vegetarian')

        recipe = sample_recipe(user2, **{
            'name': 'Danie user2',
        })
        recipe.tags.add(tag_user2)
        recipe.ingredients.add(ingredient_user2)
        payload = {
            'name': 'dobry self.user',
            'tags': [tag_self_user.slug, ],
            "ingredients": [{
                "ingredient": ingredient_self_user.slug,
                "quantity": "2kg"
            }, ],
            'description': "opis dania",
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe_self_user = models.Recipe.objects.filter(user=self.user)
        self.assertEqual(len(recipe_self_user), 1)
        recipe_user2 = models.Recipe.objects.filter(user=user2)
        self.assertEqual(len(recipe_user2), 1)

        rec_ing_self_user = models.Recipe_Ingredient.objects.\
            filter(recipe=recipe_self_user[0])
        self.assertEqual(len(rec_ing_self_user), 1)

        rec_ing_user2 = models.Recipe_Ingredient.objects.\
            filter(recipe=recipe_user2[0])
        self.assertEqual(len(rec_ing_user2), 1)

    def test_partial_recipe_update(self):
        """ test updating a recipe with PATCH """
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user, name='Vege'))
        recipe.ingredients.add(sample_ingredient(self.user, 'Cukinia'))

        new_tag = sample_tag(user=self.user, name='Curry')

        payload = {
            'name': 'Nowe danie testowe',
            'tags': [new_tag.slug, ]
        }
        url = detail_url(recipe.slug)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.name, payload['name'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_recipe_update(self):
        """ test updating a recipe with put """
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(self.user, name='Vege'))
        recipe.ingredients.add(sample_ingredient(self.user, 'Cukinia'))

        new_ing = models.Ingredient.objects.create(
            user=self.user,
            name='Czosnek'
        )
        new_ing2 = models.Ingredient.objects.create(
            user=self.user,
            name='Czosnek2'
        )
        new_tag = models.Tag.objects.create(
            name='Wegetarianski',
            user=self.user
        )
        payload = {
            'name': 'nowa nazwa dla dania',
            'tags': [new_tag.slug, ],
            "ingredients": [{
                "ingredient": new_ing.slug,
                "quantity": "10 łyżek"
            }, {
                "ingredient": new_ing2.slug,
                "quantity": "10 łyżek"
            },
            ],
            'description': "opis dania 2",
        }
        url = detail_url(recipe.slug)
        self.client.put(url, payload, format='json')
        recipe.refresh_from_db()
        self.assertEqual(recipe.name, payload['name'])
        self.assertEqual(recipe.description, payload['description'])

        tags = recipe.tags.all()
        self.assertEqual(tags[0], new_tag)
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients[0], new_ing)

    def test_full_update_with_new_ingredient_success(self):
        """ test updating recipe with new ingredient success """
        new_ingredient = 'Nowy skladnik'
        recipe = sample_recipe(self.user)
        tag = sample_tag(self.user, 'Vege')

        payload = {
            'name': 'nowa nazwa dla dania',
            'tags': [tag.slug, ],
            "ingredients": [{
                "ingredient": 'new_ingredient',
                "quantity": "10 łyżek"
            }, ],
            'description': "opis dania 2",
        }
        url = detail_url(recipe.slug)
        res = self.client.put(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(models.Ingredient.objects.all().count(), 1)

    def test_full_update_with_invalid_tag_failed(self):
        """ test updating recipe with invalid tag instance """
        user2 = get_user_model().objects.create(
            email='2@gmail.com',
            password='testpasswod',
            age=25,
            sex='Male'
        )
        tag = sample_tag(user2, 'Vege')
        recipe = sample_recipe(self.user)

        payload = {
            'name': 'nowa nazwa dla dania',
            'tags': [tag.slug, ],
            'description': "opis dania 2",
        }
        url = detail_url(recipe.slug)
        res = self.client.put(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_invalid_tags_instance(self):
        """ creating recipe with invalid tags instance """
        payload = {
            'name': 'Now danie',
            'tags': ['tekst zamiast instancji', ]
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_tag_created_by_other_user_failed(self):
        """ creating recipe with tag created by unauthenticated user
         should failed"""
        user2 = get_user_model().objects.create(
            email='2@gmail.com',
            password='testpasswod',
            age=25,
            sex='Male'
        )
        tag_user2 = sample_tag(user2, 'Tag uzytkownika 2')
        sample_tag(self.user, 'Poprawny Tag')
        ingredient = sample_ingredient(self.user, 'Czosnek')

        payload = {
            'name': 'Nowe danie',
            'tags': [tag_user2.slug, ],
            'ingredient': [
                {'ingredient': ingredient.slug, 'quantity': '2kg'},
            ]
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_new_ingredient(self):
        """ creting recipe with ingredients which are not in database yet """

        new_ingredient_name = 'Nowy Skladnik'
        new_ingredient2_name = 'Nowy Skladnik2'
        payload = {
            'name': "Nowe danie",
            'tags': [self.user_tag.slug, ],
            'ingredients': [
                {'ingredient': new_ingredient_name, 'quantity': '2kg'},
                {'ingredient': new_ingredient2_name, 'quantity': '3kg'}
            ]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        new_ingredients = models.Ingredient.objects.filter(user=self.user)

        self.assertEqual(new_ingredients.count(), 2)

    def test_create_recipe_with_doubled_ingredient_success(self):
        """ test creating recipe with passing new ingredient name which is
        already used. Test should pass """

        sample_ingredient(self.user, 'Test')
        new_ingredient_name = 'Test'
        payload = {
            'name': "Nowe danie",
            'tags': [self.user_tag.slug, ],
            'ingredients': [
                {'ingredient': new_ingredient_name, 'quantity': '2kg'},
            ]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    # def test_create_recipe_with_new_ingredient_which_has_same_slug_success(self):
    #     """ test creating recipe with new ignredient with different
    #     name but same slug eg. Sól and Sol"""
    #
    #     sample_ingredient(self.user, 'Sól')
    #     new_ingredient_name = 'Sol'
    #     payload = {
    #         'name': "Nowe danie",
    #         'tags': [self.user_tag.slug, ],
    #         'ingredients': [
    #             {'ingredient': new_ingredient_name, 'quantity': '2kg'},
    #         ]
    #     }
    #     res = self.client.post(RECIPE_URL, payload, format='json')
    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)
    #     ingredients_from_db = models.Ingredient.objects.filter(user=self.user)
    #     self.assertEqual(len(ingredients_from_db), 2)
    #     self.assertEqual(ingredients_from_db[1].slug, 'sol2')

    def test_filter_recipe_by_tags(self):
        """ Returning recipe with specific tags """

        recipe1 = sample_recipe(user=self.user, name='Pierwsza potrawa')
        recipe2 = sample_recipe(user=self.user, name='Druga potrawa')

        tag1 = sample_tag(self.user, 'Wegańskie')
        tag2 = sample_tag(self.user, 'Wegetariańskie')

        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        recipe3 = sample_recipe(self.user, name='Trzecia potrawa')

        res = self.client.get(RECIPE_URL, {'tags': f'{tag1.slug},{tag2.slug}'})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    # def test_filter_recipe_by_ingredients(self):
    #     """ returning recipe with specific ingredients """
    #
    #     recipe1 = sample_recipe(self.user, name='Pierwsza potrawa')
    #     recipe2 = sample_recipe(self.user, name='Druga potrawa')
    #
    #     ingredient1 = sample_ingredient(self.user, name='Skaldnik pierwszy')
    #     ingredient2 = sample_ingredient(self.user, name='Skaldnik drugi')
    #
    #     recipe1.ingredients.add(ingredient1)
    #     recipe2.ingredients.add(ingredient2)
    #
    #     recipe3 = sample_recipe(self.user, name='Trzecia potrawa')
    #
    #     res = self.client.get(RECIPE_URL,
    #                           {'ingredients':
    #                            f'{ingredient1.slug},{ingredient2.slug}'})
    #     serializer1 = RecipeSerializer(recipe1)
    #     serializer2 = RecipeSerializer(recipe2)
    #     serializer3 = RecipeSerializer(recipe3)
    #
    #     self.assertIn(serializer1.data, res.data)
    #     self.assertIn(serializer2.data, res.data)
    #     self.assertNotIn(serializer3.data, res.data)

    @patch('recipe.models.Ingredient.send_to_nozbe')
    def test_sending_chosen_ingredients_to_nozbe(self, mock_send_to_nozbe):
        """ test sending chosen ingredients as shopping list in nozbe
        project """

        recipe = sample_recipe(self.user)

        ing1 = sample_ingredient(user=self.user, name='Testowy 1')
        ing2 = sample_ingredient(user=self.user, name='Testowy 2')
        ing3 = sample_ingredient(user=self.user, name='Testowy 3')

        recipe.ingredients.add(ing1, ing2, ing3)

        ingredients_list = [ing1.slug, ing2.slug]

        url = reverse('recipe:recipe-send-to-nozbe', args=[recipe.slug])

        res = self.client.put(url, ingredients_list, format='json')
        serializer = IngredientSerializer([ing1, ing2], many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
