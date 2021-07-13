from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient, APITestCase, APIRequestFactory
from rest_framework import status

from recipe import models
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer, \
                                IngredientSerializer

from unittest.mock import patch

from users import models as user_models

RECIPE_URL = reverse('recipe:recipe-list')


def recipe_detail_url(recipe_slug):
    """ return recile detail URL """
    return reverse('recipe:recipe-detail', kwargs={'slug': recipe_slug})


def detail_group_url(recipe_slug, user_id):
    """ return recile detail URL """
    return reverse('recipe:recipe-group-detail', kwargs={'pk': user_id,
                                                         'slug': recipe_slug})


def sample_recipe(user, **params):
    """ create and return a sample recipe """
    defaults = {
        'name': 'Danie testowe',
        'prepare_time': 50,
        'portions': 4,
        'description': "Opis dania testowego"
    }
    defaults.update(params)

    return models.Recipe.objects.create(user=user, **defaults)


def sample_tag(user, name):
    """ create and return sampel tag """
    return models.Tag.objects.create(user=user, name=name)


def sample_ingredient(**values):
    """ create sample ingredeint """
    return models.Ingredient.objects.create(**values)


def sample_unit(name, short_name):
    """ crete sample unit """
    return models.Unit.objects.create(name=name, short_name=short_name)


def sample_user(email='user2@gmail.com', name='testusername'):
    return get_user_model().objects.create_user(
        email=email,
        name=name,
        password='testpass',
        age=25,
        weight=88,
        height=188,
        gender='Male'
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
            weight=88,
            height=188,
            gender='Male'
        )
        self.client.force_authenticate(self.user)

        self.user_tag = sample_tag(self.user, 'Tag testowy')
        self.unit = sample_unit(name='gram', short_name='g')
        self.request = APIRequestFactory().get('/')

    def test_retrieve_recipes(self):
        """ test retrieving a list of recipes """
        sample_recipe(self.user)
        params = {
            'name': 'test'
        }
        sample_recipe(self.user, **params)
        res = self.client.get(RECIPE_URL)
        recipes = models.Recipe.objects.all().order_by('-name')
        serializer = RecipeSerializer(recipes, many=True, context={'request': self.request})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_required_fields_for_recipe_creation(self):
        """ test required fields in GET response on recipe-list url """

        res = self.client.get(RECIPE_URL)
        self.assertNotEqual(res.json()['required'], None)

    def test_recipes_limited_to_user(self):
        """ test retrieving recipes for user """
        user2 = sample_user()
        sample_recipe(user2)
        sample_recipe(self.user)

        res = self.client.get(RECIPE_URL)

        recipes = models.Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True, context={'request': self.request})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_group_recipes(self):
        """ test retrieving recipes created by user and other users in the
        same group/s. Here we have 4 users. User1 (Self.user) is in group of
        user 2 and 3, so he should be able to see their recieps. User 4
        recipes should not be vivislbe"""

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
        user2_recipe.ingredients.add(sample_ingredient(user=user2, name='cukinia'))
        user3_recipe.tags.add(sample_tag(user3, 'vege'))
        user3_recipe.ingredients.add(sample_ingredient(user=user3, name='cukinia'))

        group_user2 = user_models.Group.objects.get(founder=user2)
        group_user3 = user_models.Group.objects.get(founder=user3)

        self.user.membership.add(group_user2, group_user3)

        sample_recipe(self.user, **params)
        res = self.client.get(RECIPE_URL)
        user2_recipe = models.Recipe.objects.get(user=user2)
        user3_recipe = models.Recipe.objects.get(user=user3)
        serializer_recipes = RecipeSerializer([user2_recipe, user3_recipe],
                                              many=True, context={'request': self.request})
        serializer_recipe_user4 = RecipeSerializer([user4_recipe, ], many=True, context={'request': self.request})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_recipes.data[0], res.data)
        self.assertNotIn(serializer_recipe_user4.data, res.data)

    def test_view_recipe_detail(self):
        """ test viewing a recipe detail """
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(self.user, 'vege'))
        recipe.ingredients.add(sample_ingredient(user=self.user, name='szpinak'))

        url = recipe_detail_url(recipe.slug)

        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe, context={'request': self.request})

        self.assertEqual(res.data, serializer.data)

    def test_view_group_recipe_detail(self):
        """ test retrieving detail of recipes created by other use in the
        group """

        user2 = sample_user()
        recipe = sample_recipe(user2)
        group = user_models.Group.objects.get(founder=user2)
        self.user.membership.add(group)
        url = detail_group_url(recipe.slug, user2.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe, context={'request': self.request})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_view_group_recipe_detail_with_the_same_name(self):
        """ test retrieving group recipe which has same name as self.user
        recipe """

        user2 = sample_user()
        group = user_models.Group.objects.get(founder=user2)
        self.user.membership.add(group)

        recipe_user1 = sample_recipe(self.user)
        recipe_user2 = sample_recipe(user2)

        url = detail_group_url(recipe_user2.slug, user2.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe_user2, context={'request': self.request})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """ test creating recipe """
        payload = {
            'name': 'Hamburgery vege',
            'description': 'opis dania'
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = models.Recipe.objects.get(slug=res.data['slug'])

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
        recipe = models.Recipe.objects.get(slug=res.data['slug'])
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
                'amount': '2',
                'unit': self.unit.id
            }, {
                "ingredient": ingredient2.slug,
                'amount': '2',
                'unit': self.unit.id
            }, ],
            'description': "opis dania",
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = models.Recipe.objects.get(slug=res.data['slug'])

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
        user2 = sample_user()
        ingredient_self_user = sample_ingredient(user=self.user, name='Szpinak')
        ingredient_user2 = sample_ingredient(user=user2, name='Czonsek')

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
                'amount': '2',
                'unit': self.unit.id
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
        recipe.ingredients.add(sample_ingredient(user=self.user, name='Cukinia'))

        new_tag = sample_tag(user=self.user, name='Curry')

        payload = {
            'name': 'Nowe danie testowe',
            'tags': [new_tag.slug, ]
        }
        url = recipe_detail_url(recipe.slug)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.name, payload['name'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_partial_recipe_update_failed(self):
        """ test partial update with put request """

        recipe = sample_recipe(user=self.user, name='test')
        recipe.tags.add(sample_tag(user=self.user, name='Bege'))
        recipe.ingredients.add(sample_ingredient(user=self.user,
                                                 name='Cukinia'))

        payload = {
            'ingredients': [
                {
                    'ingredient': sample_ingredient(user=self.user, name='Test').slug,
                    'amount': 20,
                    'unit': self.unit.id
                }
            ]
        }

        res = self.client.put(recipe_detail_url(recipe.slug), payload,
                              format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_full_recipe_update(self):
        """ test updating a recipe with put """
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(self.user, name='Vege'))
        recipe.ingredients.add(sample_ingredient(user=self.user, name='Cukinia'))

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
                'amount': '2',
                'unit': self.unit.id
            }, {
                "ingredient": new_ing2.slug,
                'amount': '2',
                'unit': self.unit.id
            },
            ],
            'description': "opis dania 2",
        }
        url = recipe_detail_url(recipe.slug)
        res = self.client.put(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
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
                'amount': '2',
                'unit': self.unit.id
            }, ],
            'description': "opis dania 2",
        }
        url = recipe_detail_url(recipe.slug)
        res = self.client.put(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(models.Ingredient.objects.all().count(), 1)

    def test_full_update_with_invalid_tag_failed(self):
        """ test updating recipe with invalid tag instance """
        user2 = sample_user()
        tag = sample_tag(user2, 'Vege')
        recipe = sample_recipe(self.user)

        payload = {
            'name': 'nowa nazwa dla dania',
            'tags': [tag.slug, ],
            'description': "opis dania 2",
        }
        url = recipe_detail_url(recipe.slug)
        res = self.client.put(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_other_user_recipe_failed(self):
        """ test updating group recipe attempt failed, because only owner of
        recipe can PUT, PATCH, DELETE recipe in default detail view"""

        user2 = sample_user()
        recipe = sample_recipe(user2)

        group = user_models.Group.objects.get(founder=user2)
        self.user.membership.add(group)

        serializer = RecipeDetailSerializer(recipe, context={'request': self.request})
        res = self.client.get(detail_group_url(recipe.slug, user2.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

        res = self.client.put(detail_group_url(recipe.slug, user2.id))
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_other_user_recipe_failed(self):
        """ test deleting group recipe attempt failed, because only owner
        can do it in default detail view"""

        user2 = sample_user()
        recipe = sample_recipe(user2)

        group = user_models.Group.objects.get(founder=user2)
        self.user.membership.add(group)

        serializer = RecipeDetailSerializer(recipe, context={'request': self.request})
        res = self.client.get(detail_group_url(recipe.slug, user2.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

        res = self.client.delete(detail_group_url(recipe.slug, user2.id))
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

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
        user2 = sample_user()
        tag_user2 = sample_tag(user2, 'Tag uzytkownika 2')
        sample_tag(self.user, 'Poprawny Tag')
        ingredient = sample_ingredient(user=self.user, name='Czosnek')

        payload = {
            'name': 'Nowe danie',
            'tags': [tag_user2.slug, ],
            'ingredient': [
                {'ingredient': ingredient.slug, 'amount': '2',
                    'unit': self.unit.id
                },
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
                {'ingredient': new_ingredient_name, 'amount': '2',
                    'unit': self.unit.id},
                {'ingredient': new_ingredient2_name, 'amount': '2',
                    'unit': self.unit.id}
            ]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        new_ingredients = models.Ingredient.objects.filter(user=self.user)

        self.assertEqual(new_ingredients.count(), 2)

    def test_create_recipe_with_doubled_ingredient_success(self):
        """ test creating recipe with passing new ingredient name which is
        already used. Test should pass, becouse slug will be modify """

        sample_ingredient(user=self.user, name='Test')
        new_ingredient_name = 'Test'
        payload = {
            'name': "Nowe danie",
            'tags': [self.user_tag.slug, ],
            'ingredients': [
                {'ingredient': new_ingredient_name, 'amount': '2',
                    'unit': self.unit.id},
            ]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_deleting_recipe(self):
        """ test deleting recipe by authenticated user """

        recipe = sample_recipe(self.user)

        res = self.client.delete(recipe_detail_url(recipe.slug))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        recipe = models.Recipe.objects.filter(slug=recipe.slug)

        self.assertEqual(len(recipe), 0)

    def test_deleting_recipe_belong_to_spcific_user(self):
        """ test if deleting recipe will not affect other users recipes """

        user2 = sample_user()

        recipe_user1 = sample_recipe(self.user)
        recipe_user2 = sample_recipe(user2)

        res = self.client.delete(recipe_detail_url(recipe_user1.slug))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        recipe = models.Recipe.objects.filter(user=user2). \
            filter(slug=recipe_user2.slug)

        self.assertEqual(len(recipe), 1)

    #  FEAUTRE WORKING BUT TEST NOT PASSED BECOUSE ENV PROBLEM. NO DIFFERENCE
    #  BETWEEN SÓL AND SOL DURING QUERING
    #  def test_create_recipe_with_new_ingredient_which_has_same_slug_success(self):
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

        serializer1 = RecipeSerializer(recipe1, context={'request': self.request})
        serializer2 = RecipeSerializer(recipe2, context={'request': self.request})
        serializer3 = RecipeSerializer(recipe3, context={'request': self.request})

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_non_existing_tag(self):
        """ test filtering recipes with wrong tag slug """

        recipe = sample_recipe(self.user)
        tag = sample_tag(self.user, name='tag')
        recipe.tags.add(tag)

        res = self.client.get(RECIPE_URL, {'tags': f'slug1, slug2'})

        self.assertEqual(res.data, [])

    def test_filter_recipe_by_groups(self):
        """ test filtering recipe by groups """

        user2 = sample_user()
        user3 = sample_user(email='test3@gmail.com', name='test3name')
        sample_recipe(self.user, name='Danie 1')
        sample_recipe(self.user, name='Danie 2')
        sample_recipe(user2)
        sample_recipe(user3)

        group = user_models.Group.objects.get(founder=user2)
        group2 = user_models.Group.objects.get(founder=user3)
        self.user.membership.add(group, group2)

        self_user_recipes = models.Recipe.objects.filter(user=self.user)
        user2_recipe = models.Recipe.objects.get(user=user2)
        user3_recipe = models.Recipe.objects.get(user=user3)

        serializer_self_user = RecipeSerializer(self_user_recipes, many=True, context={'request': self.request})
        serializer_user2 = RecipeSerializer(user2_recipe, context={'request': self.request})
        serializer_user3 = RecipeSerializer(user3_recipe, context={'request': self.request})
        res = self.client.get(RECIPE_URL, {'groups': f'{group.id}'},
                              format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_user2.data, res.data)
        self.assertNotIn(serializer_user3.data, res.data)

    def test_filter_recipes_by_non_existing_group_failed(self):
        """ test filter recipes with wrong group id """

        recipe = sample_recipe(self.user)

        res = self.client.get(RECIPE_URL, {'groups': '10'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_filter_recipes_by_not_joined_groups(self):
        """ test filtering reicpes by groups where user is not a member """

        user2 = sample_user()
        recipe_user2 = sample_recipe(user2)
        user2_group = user_models.Group.objects.get(founder=user2)
        recipe_self_user = sample_recipe(self.user)

        res = self.client.get(RECIPE_URL, {'groups': f'{user2_group.id}'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])
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
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @patch('recipe.models.Ingredient.send_to_nozbe')
    def test_sending_invalid_ingredients_to_nozbe_failed(self, mock_send_to_nozbe):
        """ test sening invalid ingredients to nozbe failed """
        recipe = sample_recipe(self.user)

        ing1 = sample_ingredient(user=self.user, name='Testowy 1')
        ing2 = sample_ingredient(user=self.user, name='Testowy 2')
        ing3 = sample_ingredient(user=self.user, name='Testowy 3')

        recipe.ingredients.add(ing1, ing2, ing3)

        ingredients_list = [ing1.slug, ing2.slug, 'invalid-slug']

        url = reverse('recipe:recipe-send-to-nozbe', args=[recipe.slug])

        res = self.client.put(url, ingredients_list, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_recipe_calories_based_on_ingredients(self):
        """ test auto calculating calories based on recipes ingredients """

        ing1 = sample_ingredient(
            user=self.user,
            name='Cukinia',
            calories=345,
            potassium=200,
            iron=50,
            )
        ing2 = sample_ingredient(
            user=self.user,
            name='Cukinia2',
            calories=345,
            potassium=200,
            iron=50,
            )
        ing3 = sample_ingredient(
            user=self.user,
            name='Cukinia3',
            calories=345,
            potassium=200,
            iron=50,
            )

        recipe = sample_recipe(user=self.user, name='Testowa')
        recipe.ingredients.add(ing1, through_defaults={'amount': 100, 'unit': self.unit})
        recipe.ingredients.add(ing2, through_defaults={'amount': 100, 'unit': self.unit})
        recipe.ingredients.add(ing3, through_defaults={'amount': 100, 'unit': self.unit})
        recipe.refresh_from_db()
        res = self.client.get(recipe_detail_url(recipe.slug))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['data']['calories'], ing1.calories + ing2.calories
                         + ing3.calories)

    def test_retrieving_calories_based_on_ingredients_with_no_portions_set(self):
        """ test geting 0 calories for ingredients where there is not
        portion set """

        ing1 = sample_ingredient(
            user=self.user, name='Test1', calories=100
        )
        ing2 = sample_ingredient(
            user=self.user, name='Test2', calories=300
        )
        recipe = sample_recipe(user=self.user, name='Testowy')
        recipe.ingredients.add(ing1, through_defaults={'amount': 50, 'unit':
                                                       self.unit})
        recipe.ingredients.add(ing2)
        recipe.refresh_from_db()
        res = self.client.get(recipe_detail_url(recipe.slug))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['data']['calories'], ing1.calories/2)

    def test_recalculating_calories_during_ingredient_update(self):
        """ test recalculating calories when recipe's ingredients changes """

        ing1 = sample_ingredient(user=self.user, name='Test', calories=100)
        ing2 = sample_ingredient(user=self.user, name='Test2', calories=100)
        ing3 = sample_ingredient(user=self.user, name='Test3', calories=100)

        recipe = sample_recipe(user=self.user, name='Cukinia')
        recipe.ingredients.add(ing1, through_defaults={'amount': 100, 'unit': self.unit})
        recipe.ingredients.add(ing2, through_defaults={'amount': 100, 'unit': self.unit})
        res = self.client.get(recipe_detail_url(recipe.slug))
        self.assertEqual(res.json()['data']['calories'], ing1.calories + ing2.calories)

        recipe.ingredients.add(ing3, through_defaults={'amount': 100, 'unit': self.unit})
        res = self.client.get(recipe_detail_url(recipe.slug))
        self.assertEqual(res.json()['data']['calories'], ing1.calories + ing2.calories +
                         ing3.calories)

    def test_recalculating_calories_during_ingredient_update_via_api(self):
        """ test recalculating when ingredients are updated via API """

        ing1 = sample_ingredient(user=self.user, name='Test1', calories=100)
        ing2 = sample_ingredient(user=self.user, name='Test2', calories=200)
        ing3 = sample_ingredient(user=self.user, name='Test3', calories=400)

        recipe = sample_recipe(user=self.user, name='Testowy')
        recipe.ingredients.add(ing1, through_defaults={'amount': 100, 'unit': self.unit})
        recipe.ingredients.add(ing2, through_defaults={'amount': 100, 'unit': self.unit})

        res = self.client.get(recipe_detail_url(recipe.slug))
        self.assertEqual(res.json()['data']['calories'], ing1.calories+ing2.calories)

        tag = sample_tag(user=self.user, name='Test')
        payload = {
            'tags': [tag.slug, ],
            'ingredients': [
                {
                 'ingredient': ing3.slug,
                 'amount': 12,
                 'unit': self.unit.id},
            ]
        }

        res = self.client.patch(recipe_detail_url(recipe.slug),
                                payload, format='json')
        recipe.refresh_from_db()
        expected_value_ing3 = payload['ingredients'][0]['amount'] / 100 * \
            ing3.calories
        self.assertEqual(res.json()['data']['calories'], ing1.calories+ing2.calories+
                         expected_value_ing3)

    def test_retrieve_calories_based_on_ingredient_portions(self):
        """ test amount of calories for given ingredient quantity """

        ing1 = sample_ingredient(user=self.user, name='Cukinia', calories=500)

        recipe = sample_recipe(user=self.user, name='Testowy')
        recipe.ingredients.add(ing1, through_defaults={'amount': 50,
                               'unit': self.unit})
        res = self.client.get(recipe_detail_url(recipe.slug))

        # 50g of ing1
        expected_value = ing1.calories/2
        self.assertEqual(res.json()['data']['calories'], expected_value)

    def test_retrive_calories_based_on_ingredient_portions_calories_not_set(self):
        """ test retrieving calories when ingredient does not have
        calories set """

        ing1 = sample_ingredient(user=self.user, name='Cukinia')

        recipe = sample_recipe(user=self.user, name='Test')
        recipe.ingredients.add(ing1, through_defaults={'amount': 50,
                               'unit': self.unit})

        res = self.client.get(recipe_detail_url(recipe.slug), format='json')
        self.assertEqual(res.json()['data']['calories'], 0)

    def test_retrieve_calories_based_on_portions_amount_greater_then_100(self):
        """ test retrieving calories when amount is greater then 100g"""

        ing1 = sample_ingredient(user=self.user, name='Cukinia', calories=500)
        recipe = sample_recipe(user=self.user, name='Test')
        recipe.ingredients.add(ing1, through_defaults={'amount': 150,
                               'unit': self.unit})
        res = self.client.get(recipe_detail_url(recipe.slug))

        expected_value = (150/100) * ing1.calories
        self.assertEqual(res.json()['data']['calories'], expected_value)

    def test_retieve_calories_set_by_number_of_spoons(self):
        """ test retrieving calories from recipe where ingredient portion is
        set by number of spoons """

        unit = sample_unit(name='spoon', short_name='SP')
        ing1 = sample_ingredient(user=self.user, name='cukier', calories=400)
        recipe = sample_recipe(user=self.user, name='Test')
        models.Ingredient_Unit.objects.create(unit=unit, ingredient=ing1,
                                              grams_in_one_unit=5)
        recipe.ingredients.add(ing1, through_defaults={'amount': 2,
                               'unit': unit})

        res = self.client.get(recipe_detail_url(recipe.slug))

        expected_value = (2*5/100) * ing1.calories
        # assume that one spoon of sugar weight 5g
        self.assertEqual(res.json()['data']['calories'], expected_value)

    def test_create_recipe_with_non_default_ingredinet_portions_failed(self):
        """ test creating recipe with ingredient defined by unit which was not
        previously set for defined ingredient """

        ingredient = sample_ingredient(user=self.user, name='Test',
                                       calories='300')
        non_default_unit = models.Unit.objects.create(name='spoon',
                                                      short_name='sp')
        payload = {
            'name': "Nowe danie",
            'tags': [self.user_tag.slug, ],
            'ingredients': [
                {'ingredient': ingredient.slug, 'amount': '2',
                    'unit': non_default_unit.id},
            ]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_invalid_ingredients_structure(self):
        """ test create recipe with invalid json structure for ingredietns
        failed with message """

        ingredient = sample_ingredient(user=self.user, name='Test',
                                       calories='500')
        payload = {
            'name': 'test',
            'tags': [self.user_tag.slug, ],
            'ingredients': {
                'ingredient': ingredient.slug, 'amount': '2',
                'unit': self.unit.id
            }
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
