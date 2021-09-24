from django.test import SimpleTestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from unittest.mock import patch

from recipe import services


class RecipeServicesTests(SimpleTestCase):

    def setUp(self):
        self.user = get_user_model()

    @patch('recipe.models.Recipe.objects')
    def test_check_if_name_exists_method(self, mock):
        recipe_service = services.RecipeService(user=1, data=None)
        self.assertTrue(recipe_service._check_if_name_exists('test'))
