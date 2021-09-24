from django.test import SimpleTestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from unittest.mock import patch

from recipe import selectors


class RecipeSelectorsTests(SimpleTestCase):

    def setUp(self):
        self.user = get_user_model()

    @patch('recipe.models.Recipe.objects.get')
    def test_recipe_get_selector_with_valid_params_success(self, mock):
        self.assertTrue(selectors.recipe_get(user=self.user, slug='string'))

    def test_recipe_get_selector_with_invalid_user_type_failed(self):
        with self.assertRaises(ValidationError):
            selectors.recipe_get(user='test', slug='1232')

    @patch('recipe.models.Recipe.objects.filter')
    @patch('users.selectors.group_get_membership')
    @patch('users.selectors.group_retrieve_founders')
    def test_recipe_list_selector_valid_params_success(self, mock1, mock2,
                                                       mock3):
        mock1.return_value = 1
        self.assertTrue(selectors.recipe_list(user=self.user))

    @patch('users.selectors.group_get_by_user_id')
    def test_recipe_check_if_user_can_be_retreive_invalid_recipe_creator_group_output(self, mock):
        mock.return_value = 'string'
        with self.assertRaises(ValidationError):
            selectors.recipe_check_if_user_can_retrieve(self.user, 'whatever')
