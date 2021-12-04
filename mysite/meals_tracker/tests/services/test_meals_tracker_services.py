import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError

from meals_tracker.models import MealCategory, Meal
from meals_tracker.services import (
    CreateMealDto,
    CreateMeal,
    UpdateMealDto,
    UpdateMeal,
    UpdateMealRecipeDto,
    UpdateMealRecipe,
    AddRecipesToMeal,
    AddRecipesToMealDto,
    UpdateMealIngredientDto,
    UpdateMealIngredient,
    DeleteMeal,
    RemoveRecipeFromMeal,
    RemoveIngredientFromMeal,
)
from recipe.models import Recipe, Ingredient
from recipe import selectors as recipe_selectors


class MealsTrackerServicesTests(TestCase):

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test100@gmail.com',
            name='testname100',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,)
        self.today = datetime.date.today()

    @staticmethod
    def _create_recipe(
            user: get_user_model,
            name: str = 'test recipe',
            calories: int = 1000
            ) -> None:
        """ create recipe with fixed calories """
        return Recipe.objects.create(
            user=user,
            name=name,
            slug=slugify(name),
            calories=calories,
            portions=4,
        )

    @staticmethod
    def _create_category(name: str = 'breakfast') -> None:
        return MealCategory.objects.create(name=name)

    @staticmethod
    def _create_ingredient(user: get_user_model, name: str = 'test ing', calories: int = 500) -> Ingredient:
        ingredient = Ingredient.objects.create(
            user=user,
            name=name,
            slug=slugify(name),
            calories=calories
        )
        unit = recipe_selectors.unit_get_default()
        ingredient.units.add(unit, through_defaults={'grams_in_one_unit': 100})
        return ingredient

    def _create_meal(self, user: get_user_model) -> Meal:
        recipe = self._create_recipe(user=user)
        ingredient = self._create_ingredient(user=user)
        unit = recipe_selectors.unit_get_default()
        dto = CreateMealDto(
            user=self.user,
            date=self.today,
            category=self._create_category().id,
            recipes=[{'recipe': recipe.id, 'portion': 1}],
            ingredients=[{'ingredient': ingredient.id,
                          'unit': unit.id, 'amount': 100}]
        )
        return CreateMeal().create(dto)

    def test_create_meals_from_two_recipes_sucess(self) -> None:
        recipe1 = self._create_recipe(self.user)
        recipe2 = self._create_recipe(self.user, name='recipe2')
        breakfast = self._create_category()
        dto = CreateMealDto(
            user=self.user,
            date=self.today,
            category=breakfast.id,
            recipes=[
                {'recipe': recipe1.id, 'portion': 1},
                {'recipe': recipe2.id, 'portion': 1},
            ]
            )
        service = CreateMeal()
        meal = service.create(dto)
        expected_calories = recipe_selectors.recipe_calculate_calories_based_on_portion(
            dto.recipes[0]['portion'], recipe1)
        expected_calories += recipe_selectors.recipe_calculate_calories_based_on_portion(
            dto.recipes[1]['portion'], recipe2)
        self.assertEqual(
            meal.calories, expected_calories)

    def test_create_recipe_without_any_recipe_or_ingredient_failed(self) -> None:
        with self.assertRaises(ValidationError):
            CreateMealDto(
                user=self.user,
                date=self.today,
                category=1,
            )

    def test_create_meal_from_non_existing_recipe_failed(self) -> None:
        with self.assertRaises(ValidationError):
            dto = CreateMealDto(
                user=self.user,
                date=self.today,
                category=self._create_category().id,
                recipes=[{'recipe': 1, 'portion': 1}]
            )
            CreateMeal().create(dto)

    def test_create_meal_from_recipe_with_incorrect_portion_failed(self) -> None:
        recipe = self._create_recipe(self.user)
        with self.assertRaises(ValidationError):
            dto = CreateMealDto(
                user=self.user,
                date=self.today,
                category=self._create_category().id,
                recipes=[{'recipe': recipe.id, 'portion': -1}]
            )
            CreateMeal().create(dto)

    def test_create_meal_from_non_available_recipe_failed(self) -> None:
        user2 = get_user_model().objects.create_user(
            email='test2100@gmail.com',
            name='testname2',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,)
        recipe1 = self._create_recipe(user2)
        with self.assertRaises(ValidationError):
            dto = CreateMealDto(
                user=self.user,
                date=self.today,
                category=self._create_category().id,
                recipes=[
                    {'recipe': recipe1.id, 'portion': 1},
                ]
                )
            CreateMeal().create(dto)

    def test_create_meal_with_non_existing_category_failed(self) -> None:
        recipe = self._create_recipe(self.user)
        with self.assertRaises(ValidationError):
            dto = CreateMealDto(
                user=self.user,
                date=self.today,
                category=10,
                recipes=[{'recipe': recipe.id, 'portion': 1}]
            )
            CreateMeal().create(dto)

    def test_create_meal_from_ingredients_success(self) -> None:
        ingredient = self._create_ingredient(self.user)
        ingredient2 = self._create_ingredient(self.user, name='ingredient2')
        unit = recipe_selectors.unit_get_default()
        dto = CreateMealDto(
            user=self.user,
            date=self.today,
            category=self._create_category().id,
            ingredients=[
                {'ingredient': ingredient.id, 'unit': unit.id, 'amount': 100},
                {'ingredient': ingredient2.id, 'unit': unit.id, 'amount': 200}
            ]
        )
        service = CreateMeal()
        meal = service.create(dto)
        self.assertEqual(meal.calories, ingredient.calories
                         + ingredient2.calories * 2)

    def test_create_meal_from_non_existing_ingredients_failed(self) -> None:
        unit = recipe_selectors.unit_get_default()
        with self.assertRaises(ValidationError):
            dto = CreateMealDto(
                user=self.user,
                date=self.today,
                category=self._create_category().id,
                ingredients=[
                    {'ingredient': 1, 'unit': unit.id, 'amount': 100},
                ]
            )
            CreateMeal().create(dto)

    def test_create_meal_from_ingredient_with_invalid_unit_failed(self) -> None:
        ingredient = self._create_ingredient(self.user)
        with self.assertRaises(ValidationError):
            dto = CreateMealDto(
                user=self.user,
                date=self.today,
                category=self._create_category().id,
                ingredients=[
                    {'ingredient': ingredient.id, 'unit': 1, 'amount': 100},
                ]
            )
            CreateMeal().create(dto)

    def test_create_meal_from_recipe_and_ingredient_success(self) -> None:
        ingredient = self._create_ingredient(self.user)
        ingredient2 = self._create_ingredient(self.user, name='ingredient2')
        recipe = self._create_recipe(user=self.user)
        unit = recipe_selectors.unit_get_default()
        dto = CreateMealDto(
            user=self.user,
            date=self.today,
            category=self._create_category().id,
            recipes=[
                {'recipe': recipe.id, 'portion': 1}
            ],
            ingredients=[
                {'ingredient': ingredient.id, 'unit': unit.id, 'amount': 100},
                {'ingredient': ingredient2.id, 'unit': unit.id, 'amount': 200}
            ]
        )
        service = CreateMeal()
        meal = service.create(dto)
        expected_calories = recipe.calories * \
            dto.recipes[0]['portion']/recipe.portions
        expected_calories += ingredient.calories + ingredient2.calories * 2
        self.assertEqual(meal.calories, expected_calories)

    def test_add_aditional_recipe_to_meal(self) -> None:
        meal = self._create_meal(self.user)
        expected_calories = meal.calories
        new_recipe = self._create_recipe(self.user, name='new', calories=1000)
        dto = AddRecipesToMealDto(
            user=self.user,
            recipes=[{'recipe': new_recipe.id, 'portion': 1}]
        )
        service = AddRecipesToMeal()
        service.add(meal, dto)
        self.assertEqual(meal.calories, expected_calories
                         + new_recipe.calories * dto.recipes[0]['portion']/new_recipe.portions)

    def test_update_meal_category_success(self) -> None:
        meal = self._create_meal(self.user)
        new_category = self._create_category(name='dinner')

        dto = UpdateMealDto(
            category=new_category.id
        )
        service = UpdateMeal()
        service.update(meal, dto)
        self.assertEqual(meal.category, new_category)

    def test_update_meal_recipe_success(self) -> None:
        meal = self._create_meal(self.user)
        expected_calories_without_recipe = meal.ingredients.all()[0].calories
        meal_recipe_to_be_updated = meal.recipe_portion.get(meal=meal)
        dto = UpdateMealRecipeDto(
            portion=4
        )
        service = UpdateMealRecipe()
        expected_calories = expected_calories_without_recipe + \
            meal_recipe_to_be_updated.recipe.calories
        service.update(meal_recipe_to_be_updated, dto)
        self.assertEqual(meal.calories, expected_calories)

    def test_update_meal_ingredient_success(self) -> None:
        meal = self._create_meal(self.user)
        meal_ingredient_to_be_updated = meal.ingredientamount_set.get(
            meal=meal)
        unit = meal_ingredient_to_be_updated.ingredient.units.all()[0]
        expected_calories = meal.calories - \
            meal_ingredient_to_be_updated.ingredient.calories
        dto = UpdateMealIngredientDto(
            unit=unit.id,
            amount=200,
        )
        service = UpdateMealIngredient()
        service.update(meal_ingredient_to_be_updated, dto)
        expected_calories += meal_ingredient_to_be_updated.ingredient.calories*2
        self.assertEqual(meal.calories, expected_calories)

    def test_update_meal_ingredient_with_incorrect_unit_id_failed(self) -> None:
        meal = self._create_meal(self.user)
        meal_ingredient_to_be_updated = meal.ingredientamount_set.get(
            meal=meal)
        dto = UpdateMealIngredientDto(
            unit=1,
            amount=200,
        )
        service = UpdateMealIngredient()
        with self.assertRaises(ValidationError):
            service.update(meal_ingredient_to_be_updated, dto)

    def test_deleting_meal_success(self) -> None:
        meal = self._create_meal(self.user)
        DeleteMeal().delete(meal)
        with self.assertRaises(Meal.DoesNotExist):
            meal.refresh_from_db()

    def test_deleting_recipe_from_meal_success(self) -> None:
        meal = self._create_meal(self.user)
        recipe_to_be_deleted_from_meal = meal.recipes.all()[0]
        RemoveRecipeFromMeal().remove(recipe_to_be_deleted_from_meal)
        with self.assertRaises(Recipe.DoesNotExist):
            meal.recipes.get(id=recipe_to_be_deleted_from_meal.id)

    def test_deleting_ingredient_from_meal_success(self) -> None:
        meal = self._create_meal(self.user)
        ingredient_to_be_deleted_from_meal = meal.ingredients.all()[0]
        RemoveIngredientFromMeal().remove(ingredient_to_be_deleted_from_meal)
        with self.assertRaises(Ingredient.DoesNotExist):
            meal.ingredients.get(id=ingredient_to_be_deleted_from_meal.id)
