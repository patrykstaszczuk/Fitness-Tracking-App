from django.test import TestCase
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from recipe.models import Recipe, Tag, Unit, Ingredient, Recipe_Ingredient
from recipe.services import (
    CreateRecipeDto,
    CreateRecipe,
    CreateIngredientDto,
    CreateIngredient,
    UpdateRecipe,
    AddTagsToRecipe,
    AddingTagsToRecipeInputDto,
    RemoveTagsFromRecipe,
    RemoveTagsFromRecipeInputDto,
    AddIngredientsToRecipeDto,
    AddIngredientsToRecipe,
    RemoveIngredientsFromRecipe,
    RemoveIngredientsFromRecipeDto,
    UpdateRecipeIngredientDto,
    UpdateRecipeIngredient,
    DeleteRecipe
)


class RecipeServicesTests(TestCase):

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='testname',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,
        )

    @staticmethod
    def _create_recipe(user: get_user_model, name: str = 'test recipe') -> None:
        dto = CreateRecipeDto(
            user=user,
            name=name,
            portions=4,
            prepare_time=45,
        )
        return CreateRecipe().create(dto)

    @staticmethod
    def _create_ingredient(user: get_user_model, name: str = 'test ingredient') -> None:
        dto = CreateIngredientDto(
            user=user,
            name=name,
            calories=100
        )
        return CreateIngredient().create(dto)

    @staticmethod
    def _create_unit(name: str = 'gram') -> None:
        return Unit.objects.create(
            name=name
        )

    @staticmethod
    def _map_ingredient_with_unit(ingredient: Ingredient, unit: Unit) -> None:
        ingredient.units.add(unit, through_defaults={'grams_in_one_unit': 100})

    def test_create_recipe_service(self) -> None:
        dto = CreateRecipeDto(
            user=self.user,
            name='testrecipe',
            portions=4,
            prepare_time=45,
            description='text'
        )
        service = CreateRecipe()
        recipe = service.create(dto)

        self.assertEqual(recipe.name, dto.name)
        self.assertEqual(recipe.slug, slugify(dto.name))

    def test_create_recipe_integrity_error_raise_exception(self) -> None:
        dto = CreateRecipeDto(
            user=self.user,
            name='testrecipe',
            portions=4,
            prepare_time=45,
            description='text'
        )
        service = CreateRecipe()
        service.create(dto)
        with self.assertRaises(ValidationError):
            service.create(dto)

    def test_create_recipe_with_negative_portions_raise_error(self) -> None:
        with self.assertRaises(ValidationError):
            CreateRecipeDto(
                user=self.user,
                name='testrecipe',
                portions=-1,
                prepare_time=45,
                description='text'
            )

    def test_create_recipe_with_negative_prepare_time_raise_error(self) -> None:
        with self.assertRaises(ValidationError):
            CreateRecipeDto(
                user=self.user,
                name='testrecipe',
                portions=4,
                prepare_time=-1,
                description='text'
            )

    def test_update_recipe_success(self) -> None:
        recipe = self._create_recipe(self.user)
        dto = CreateRecipeDto(
            user=self.user,
            name=recipe.name,
            portions=10,
            prepare_time=recipe.prepare_time,
            description=recipe.description,
        )
        service = UpdateRecipe()
        recipe = service.update(recipe, dto)
        self.assertEqual(recipe.portions, dto.portions)

    def test_adding_tags_to_recipe_success(self) -> None:
        tag1 = Tag.objects.create(user=self.user, name='tag1')
        tag2 = Tag.objects.create(user=self.user, name='tag2')
        recipe = self._create_recipe(self.user)
        dto = AddingTagsToRecipeInputDto(
            user=self.user,
            tag_ids=[tag1.id, tag2.id]
        )
        service = AddTagsToRecipe()
        service.add(recipe, dto)
        self.assertEqual(recipe.tags.all().count(), 2)

    def test_adding_invalid_tag_raise_error(self) -> None:
        with self.assertRaises(ValidationError):
            AddingTagsToRecipeInputDto(
                user=self.user,
                tag_ids=[1, 2, 3]
            )

    def test_removing_tags_from_recipe_success(self) -> None:
        tag1 = Tag.objects.create(user=self.user, name='tag1')
        tag2 = Tag.objects.create(user=self.user, name='tag2')
        tag3 = Tag.objects.create(user=self.user, name='tag3')
        recipe = self._create_recipe(self.user)
        recipe.tags.add(tag1, tag2, tag3)
        dto = RemoveTagsFromRecipeInputDto(
            tag_ids=[tag1.id, tag2.id]
        )
        service = RemoveTagsFromRecipe()
        service.remove(recipe, dto)
        self.assertEqual(recipe.tags.all().count(), 1)

    @patch('recipe.selectors.ingredient_is_mapped_with_unit')
    def test_adding_ingredient_to_recipe_success(self, mock) -> None:
        mock.return_value = True
        recipe = self._create_recipe(self.user)
        ingredient = self._create_ingredient(self.user)
        unit = self._create_unit()
        dto = AddIngredientsToRecipeDto(
            user=self.user,
            ingredients=[
                {
                    'ingredient': ingredient.id,
                    'unit': unit.id,
                    'amount': 100
                }
            ]
        )
        service = AddIngredientsToRecipe()
        service.add(recipe, dto)
        self.assertEqual(recipe.ingredients.all().count(), 1)
        self.assertEqual(recipe.ingredients_quantity.get(ingredient=ingredient).amount,
                         dto.ingredients[0]['amount'])

    def test_adding_non_existing_ingredient_to_recipe_failed(self) -> None:
        with self.assertRaises(ValidationError):
            AddIngredientsToRecipeDto(
                user=self.user,
                ingredients=[
                    {
                        'ingredient': 1,
                        'unit': 1,
                        'amount': 100
                    }
                ]
            )

    def test_adding_ingredient_with_invalid_unit_to_recipe_failed(self) -> None:
        ingredient = self._create_ingredient(self.user)
        with self.assertRaises(ValidationError):
            AddIngredientsToRecipeDto(
                user=self.user,
                ingredients=[
                    {
                        'ingredient': ingredient.id,
                        'unit': 1,
                        'amount': 100
                    }
                ]
            )

    def test_adding_ingredient_with_no_mapped_unit_failed(self) -> None:
        ingredient = self._create_ingredient(self.user)
        unit = self._create_unit()
        with self.assertRaises(ValidationError):
            AddIngredientsToRecipeDto(
                user=self.user,
                ingredients=[
                    {
                        'ingredient': ingredient.id,
                        'unit': unit.id,
                        'amount': 100
                    }
                ]
            )

    def test_removing_ingredient_from_recipe(self) -> None:
        recipe = self._create_recipe(user=self.user)
        ingredient1 = self._create_ingredient(user=self.user)
        unit = self._create_unit(name='gram')
        recipe.ingredients.add(ingredient1.id, through_defaults={
                               'unit_id': unit.id, 'amount': 100})
        dto = RemoveIngredientsFromRecipeDto(
            ingredient_ids=[ingredient1.id, ]
        )
        service = RemoveIngredientsFromRecipe()
        service.remove(recipe, dto)
        self.assertEqual(recipe.ingredients.all().count(), 0)

    def test_updating_recipe_ingredients(self) -> None:
        recipe = self._create_recipe(user=self.user)
        ingredient1 = self._create_ingredient(user=self.user)
        unit = self._create_unit(name='gram')
        self._map_ingredient_with_unit(ingredient1, unit)
        recipe.ingredients.add(ingredient1.id, through_defaults={
                               'unit_id': unit.id, 'amount': 100})
        recipe_ingredient_instance = Recipe_Ingredient.objects.get(
            recipe=recipe, ingredient=ingredient1)
        new_unit = self._create_unit(name='new')
        self._map_ingredient_with_unit(ingredient1, new_unit)
        dto = UpdateRecipeIngredientDto(
            ingredient_id=recipe_ingredient_instance.ingredient_id,
            unit_id=new_unit.id,
            amount=500,
        )
        service = UpdateRecipeIngredient()
        service.update(recipe_ingredient_instance, dto)
        self.assertEqual(recipe_ingredient_instance.unit_id, dto.unit_id)
        self.assertEqual(recipe_ingredient_instance.amount, dto.amount)

    def test_updating_recipe_ingredient_with_new_unit_without_mapping_failed(self) -> None:
        recipe = self._create_recipe(self.user)
        ingredient1 = self._create_ingredient(self.user)
        unit = self._create_unit(name='gram')
        self._map_ingredient_with_unit(ingredient1, unit)
        recipe.ingredients.add(ingredient1.id, through_defaults={
                               'unit_id': unit.id, 'amount': 100})
        recipe_ingredient_instance = Recipe_Ingredient.objects.get(
            recipe=recipe, ingredient=ingredient1)
        with self.assertRaises(ValidationError):
            UpdateRecipeIngredientDto(
                ingredient_id=recipe_ingredient_instance.ingredient_id,
                unit_id=1,
                amount=500,
            )

    def test_deleting_recipe_success(self) -> None:
        recipe = self._create_recipe(self.user)
        service = DeleteRecipe()
        service.delete(recipe)
        with self.assertRaises(Recipe.DoesNotExist):
            recipe.refresh_from_db()
