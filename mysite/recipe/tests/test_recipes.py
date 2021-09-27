from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify

from rest_framework.test import force_authenticate
from rest_framework.test import APIClient
from rest_framework import status

from recipe.models import Recipe, Tag, Ingredient, Unit
from recipe.services import IngredientService


def recipe_detail_url(slug: str) -> str:
    """ generate recipe detail url """
    return reverse('recipe:recipe-detail', kwargs={'slug': slug})


def group_recipe_detail_url(user: get_user_model, slug: str) -> str:
    """ generate group recipe detail url """
    return reverse('recipe:group-recipe-detail',
                   kwargs={'slug': slug, 'pk': user.id})


def recipe_update_url(slug: str) -> str:
    """ generate url for recipe update """
    return reverse('recipe:recipe-update', kwargs={'slug': slug})


def recipe_delete_url(slug: str) -> str:
    """ generate url for deleting recipe """
    return reverse('recipe:recipe-delete', kwargs={'slug': slug})


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


def sample_ingredient(user: get_user_model, name='str', calories=100, **kwargs) -> Ingredient:
    """ create sample ingredient """
    slug = slugify(name)
    ing = Ingredient.objects.create(user=user, name=name, slug=slug,
                                    calories=calories, **kwargs)
    IngredientService._set_default_unit(ing)
    return ing


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

    def test_get_other_user_recipe_invalid_type_failed(self):
        url = reverse('recipe:group-recipe-detail',
                      kwargs={'slug': 'slug', 'pk': 'string'})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

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
            'tags': [tag.slug, ],
            'portions': 4
        }
        res = self.client.post(RECIPE_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_ingredients(self):
        ingredient1 = sample_ingredient(user=self.auth_user, name='test')
        ingredient2 = sample_ingredient(user=self.auth_user, name='test2')
        tag = sample_tag(user=self.auth_user, name='tag')
        unit = ingredient1.units.all()[0]
        payload = {
            "name": "new",
            "tags": [tag.slug, ],
            "ingredients": [
                {"ingredient": ingredient1.slug, "unit": unit.id, "amount": 100},
                {"ingredient": ingredient2.slug, "unit": unit.id, "amount": 100}

            ],
            "portions": 4
        }
        res = self.client.post(RECIPE_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(len(res.data['ingredients']), 2)

    def test_create_recipe_with_ingredients_created_by_other_user(self):
        user2 = sample_user('2@gmail.com', 'test')
        user2_ingredient = sample_ingredient(user2, 'user2 ing')
        ingredient = sample_ingredient(self.auth_user, 'ingredient')
        unit = ingredient.units.all()[0]
        payload = {
            'name': 'recipe',
            'tags': [sample_tag(self.auth_user, 'tag').slug, ],
            'ingredients': [
                {'ingredient': ingredient.slug, "unit": unit.id, "amount": 100},
                {'ingredient': user2_ingredient.slug,
                    "unit": unit.id, "amount": 100},

            ],
            'portions': 4
        }
        res = self.client.post(RECIPE_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(len(res.data['ingredients']), 2)

    def test_recipe_create_real_life_scenario(self):
        user2 = sample_user('2@gmail.com', 'test')
        user2_ingredient = sample_ingredient(user2, 'user2 ing')
        ingredient = sample_ingredient(self.auth_user, 'ingredient')
        ingredient2 = sample_ingredient(self.auth_user, 'ingredient2')
        unit = ingredient.units.all()[0]
        unit2 = Unit.objects.create(name='spoon')
        ingredient2.units.add(unit2, through_defaults={
                              'grams_in_one_unit': 50})
        tag = sample_tag(self.auth_user, 'tag')

        payload = {
            'name': 'recipe',
            'portions': 4,
            'prepare_time': 45,
            'tags': [tag.slug, ],
            'ingredients': [
                {'ingredient': ingredient.slug, "unit": unit.id, "amount": 100},
                {'ingredient': ingredient2.slug, "unit": unit2.id, "amount": 100},
                {'ingredient': user2_ingredient.slug,
                    "unit": unit.id, "amount": 100},

            ],
        }
        res = self.client.post(RECIPE_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(len(res.data['ingredients']), 3)

    def test_total_recipe_calories_with_ingredients(self):
        ing1 = sample_ingredient(self.auth_user, 'ing1', calories=1000)
        ing2 = sample_ingredient(self.auth_user, 'ing2', calories=500)
        tag = sample_tag(self.auth_user, 'tag')
        unit = ing1.units.all()[0]
        payload = {
            'name': 'recipe',
            'portions': 4,
            'tags': [tag.slug],
            'ingredients': [
                {'ingredient': ing1.slug, "unit": unit.id, "amount": 100},
                {'ingredient': ing2.slug, "unit": unit.id, "amount": 100},
            ]
        }
        res = self.client.post(RECIPE_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]
        res = self.client.get(url)
        calories_expected_value = ing1.calories * 1 + ing2.calories * 1
        self.assertEqual(res.data['calories'], calories_expected_value)

    def test_total_recipe_calories_with_non_default_ingredient(self):
        unit = Unit.objects.create(name='spoon')
        ing1 = sample_ingredient(self.auth_user, 'ing', calories=500)
        ing1.units.add(unit, through_defaults={'grams_in_one_unit': 20})
        tag = sample_tag(self.auth_user, 'tag')

        payload = {
            'name': 'recipe',
            'portions': 4,
            'tags': [tag.slug],
            'ingredients': [
                {'ingredient': ing1.slug, "unit": unit.id, "amount": 2},  # two spoon
            ]
        }
        res = self.client.post(RECIPE_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        url = res._headers['location'][1]
        res = self.client.get(url)
        calories_expected_value = ing1.calories/(100/20) * 2
        self.assertEqual(res.data['calories'], calories_expected_value)

    def test_create_recipe_with_non_existins_ingredient_failed(self):
        tag = sample_tag(self.auth_user, 'tag')

        payload = {
            'name': 'test',
            'portions': 4,
            'tags': [tag.slug, ],
            'ingredients': [{'ingredient': 'string', 'unit': 1, 'amount': '1'}]
        }
        res = self.client.post(RECIPE_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_recipe_with_invalid_unit_failed(self):
        unit = Unit.objects.create(name='test')
        ingredient = sample_ingredient(self.auth_user, 'ing')
        tag = sample_tag(self.auth_user, 'tag')

        payload = {
            'name': 'test',
            'portions': 4,
            'tags': [tag.slug, ],
            'ingredients': [{'ingredient': ingredient.slug, 'unit': unit.id, 'amount': '100'}]
        }
        unit.delete()
        res = self.client.post(RECIPE_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_recipe_without_unit_failed(self):
        ingredient = sample_ingredient(self.auth_user, 'ing')
        tag = sample_tag(self.auth_user, 'tag')

        payload = {
            'name': 'test',
            'portions': 4,
            'tags': [tag.slug, ],
            'ingredients': [{'ingredient': ingredient.slug, 'amount': '100'}]
        }
        res = self.client.post(RECIPE_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_without_amount_failed(self):
        unit = Unit.objects.create(name='test')
        ingredient = sample_ingredient(self.auth_user, 'ing')
        tag = sample_tag(self.auth_user, 'tag')

        payload = {
            'name': 'test',
            'portions': 4,
            'tags': [tag.slug, ],
            'ingredients': [{'ingredient': ingredient.slug, 'unit': unit.id}]
        }
        unit.delete()
        res = self.client.post(RECIPE_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_full_recipe_update(self):
        recipe = sample_recipe(self.auth_user, 'name', 4)
        ing = sample_ingredient(user=self.auth_user, name='test', calories=100)
        unit = ing.units.all()[0]
        recipe.ingredients.add(ing, through_defaults={
                               'unit': unit, 'amount': 100})
        new_ing = sample_ingredient(
            user=self.auth_user, name='new ing', calories=200)
        payload = {
            'name': 'new name',
            'portions': 4,
            'tags': [sample_tag(self.auth_user, 'new tag').slug, ],
            'ingredients': [{'ingredient': new_ing.slug, 'unit': unit.id, 'amount': 100}]
            }
        res = self.client.put(recipe_update_url(
            recipe.slug), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(len(res.data['ingredients']), 1)

    def test_partial_recipe_update(self):
        recipe = sample_recipe(self.auth_user, 'name', 4)
        ing = sample_ingredient(user=self.auth_user, name='test', calories=100)
        unit = ing.units.all()[0]
        recipe.ingredients.add(ing, through_defaults={
                               'unit': unit, 'amount': 100})
        new_ing = sample_ingredient(
            user=self.auth_user, name='new ing', calories=200)
        payload = {
            'name': 'new name',
            'ingredients': [{'ingredient': new_ing.slug, 'unit': unit.id, 'amount': 100}]
            }
        res = self.client.patch(recipe_update_url(
            recipe.slug), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(len(res.data['ingredients']), 2)

    def test_recipe_put_update_with_already_taken_name(self):
        sample_recipe(self.auth_user, 'recipe')
        recipe = sample_recipe(self.auth_user, 'other recipe')

        payload = {
            'name': 'recipe'
        }
        res = self.client.patch(recipe_update_url(
            recipe.slug), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deleting_recipe(self):
        recipe = sample_recipe(self.auth_user, name='test')

        res = self.client.delete(recipe_delete_url(recipe.slug))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipes = Recipe.objects.filter(user=self.auth_user).exists()
        self.assertFalse(recipes)

    def test_deleting_other_user_recipe_failed(self):
        user2 = sample_user('2@gmail.com', 'test')
        recipe = sample_recipe(user2, 'test')

        res = self.client.delete(recipe_delete_url(recipe.slug))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
