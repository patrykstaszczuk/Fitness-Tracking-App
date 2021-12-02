from dataclasses import dataclass
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from meals_tracker.models import Meal, RecipePortion, IngredientAmount
from django.db import IntegrityError
from recipe.models import Recipe, Ingredient_Unit
from recipe.selectors import (
    recipe_calculate_calories_based_on_portion,
    recipe_list,
    ingredient_list,
    ingredient_calculate_calories,
    unit_list,
    ingredient_calculate_calories
    )
import datetime
from abc import ABC


@dataclass
class CreateMealDto:
    recipe = int
    portion = int
    ingredient = int
    unit = int
    amount = int

    user: get_user_model
    date: datetime
    category: int
    recipes: list[dict[str, recipe | portion]] = None
    ingredients: list[dict[str, ingredient | unit | amount]] = None

    def __post_init__(self) -> None:
        if self.recipes is None and self.ingredients is None:
            raise ValidationError(
                'Meal must include at least on recipe or ingredient')


class CreateMeal():
    def create(self, dto: CreateMealDto) -> Meal:
        try:
            meal = Meal.objects.create(
                user=dto.user,
                date=dto.date,
                category_id=dto.category
            )
        except IntegrityError:
            raise ValidationError(
                f'Category with id {dto.category} does not exists!')

        try:
            if dto.recipes:
                recipes_dto = AddRecipesToMealDto(
                    user=meal.user, recipes=dto.recipes)
                AddRecipesToMeal().add(meal, recipes_dto)

            if dto.ingredients:
                ingredients_dto = AddIngredientsToMealDto(
                    user=meal.user, ingredients=dto.ingredients)
                AddIngredientsToMeal().add(meal, ingredients_dto)
        except ValidationError as e:
            meal.delete()
            raise ValidationError(e)

        meal.save()
        return meal


@dataclass
class AddRecipesToMealDto:
    recipe = int
    portion = int

    user: get_user_model
    recipes: list[dict[str, recipe | portion]] = None

    def __post_init__(self):
        if not self.recipes:
            return
        available_recipe_for_user = recipe_list(
            user=self.user).values_list('id', flat=True)
        for item in self.recipes:
            if item['recipe'] not in available_recipe_for_user:
                raise ValidationError(
                    f'Recipe with id {item["recipe"]} does not exists or \
                    you do not have permissions to retrieve it')
            if item['portion'] < 1:
                raise ValidationError(
                    f'Incorrect portion {item["portion"]}for recipe {item["recipe"]} ')


class AddRecipesToMeal:
    def add(self, meal: Meal, dto: AddRecipesToMealDto) -> None:
        for item in dto.recipes or []:
            meal.recipes.add(item['recipe'], through_defaults={
                             'portion': item['portion']})
        dto = RecalculateMealCaloriesDto(recipes=dto.recipes)
        RecalculateMealCalories().add_recipes(dto, meal)


class RemoveRecipeFromMeal:
    def remove(self, recipe_portion: RecipePortion) -> None:
        recipe_portion.delete()


@dataclass
class AddIngredientsToMealDto:
    ingredient = int
    unit = int
    amount = int

    user: get_user_model
    ingredients: list[dict[str, ingredient | unit | amount]] = None

    def __post_init__(self):
        if not self.ingredients:
            return
        dto_ingredients_ids = set([item['ingredient']
                                   for item in self.ingredients])
        ingredients = set(ingredient_list().filter(
            id__in=dto_ingredients_ids).values_list('id', flat=True))
        if dto_ingredients_ids != ingredients:
            non_existsting_ids = list(dto_ingredients_ids - ingredients)
            raise ValidationError(
                f'Ingredient with ids {non_existsting_ids} do not exist')

        dto_units_ids = [item['unit'] for item in self.ingredients]
        available_units = unit_list().values_list('id', flat=True)
        for id in dto_units_ids:
            if id not in available_units:
                raise ValidationError(f'Unit with id {id} does not exists')


class AddIngredientsToMeal:
    def add(self, meal: Meal, dto: AddIngredientsToMealDto) -> None:
        for item in dto.ingredients or []:
            meal.ingredients.add(item['ingredient'], through_defaults={
                                     'unit_id': item['unit'], 'amount': item['amount']})
        dto = RecalculateMealCaloriesDto(ingredients=dto.ingredients)
        RecalculateMealCalories().add_ingredients(dto, meal)


class RemoveIngredientFromMeal:
    def remove(self, ingredient_amount: IngredientAmount) -> None:
        ingredient_amount.delete()


@dataclass
class RecalculateMealCaloriesDto:
    recipe = int
    portion = int
    ingredient = int
    unit = int
    amount = int

    recipes: list[dict[str, recipe | portion]] = None
    ingredients: list[dict[str, ingredient | unit | amount]] = None


class RecalculateMealCalories():
    def add_recipes(self, dto: RecalculateMealCaloriesDto, meal: Meal) -> None:
        if not dto.recipes:
            raise ValueError(
                f'You cannot use add_recipes method with recipes set to None in RecalculateMealCaloriesDto')
        recipes_ids = [item['recipe'] for item in dto.recipes]
        recipes_to_be_added = Recipe.objects.filter(id__in=recipes_ids)
        for recipe, item in zip(recipes_to_be_added, dto.recipes):
            meal.calories += recipe_calculate_calories_based_on_portion(
                item['portion'], recipe)
        meal.save()

    def add_ingredients(self, dto: RecalculateMealCaloriesDto, meal: Meal) -> None:
        if not dto.ingredients:
            raise ValueError(
                f'You cannot use add_ingredients method with ingredients set to None in RecalculateMealCaloriesDto')
        ingredients_ids = [item['ingredient']
                           for item in dto.ingredients]
        unit_ids = [item['unit'] for item in dto.ingredients]
        ingredients_with_amount = Ingredient_Unit.objects.filter(
            ingredient_id__in=ingredients_ids, unit_id__in=unit_ids).prefetch_related('ingredient', 'unit')
        for item, dto_item in zip(ingredients_with_amount, dto.ingredients):
            meal.calories += ingredient_calculate_calories(
                item.ingredient, item.unit, dto_item['amount'])
        meal.save()


@dataclass
class UpdateMealDto:
    category: int


class UpdateMeal():
    def update(self, meal: Meal, dto: UpdateMealDto) -> None:
        meal.category_id = dto.category
        try:
            meal.save()
            return meal
        except IntegrityError:
            raise ValidationError(
                f'Category with id {dto.category} does not exists')


@dataclass
class UpdateMealRecipeDto:
    portion: int

    def __post_init__(self):
        if self.portion < 1:
            raise ValidationError(f'Incorrect portion: {self.portion}')


class UpdateMealRecipe:
    def update(self, recipe_portion: RecipePortion, dto: UpdateMealRecipeDto) -> None:
        if not recipe_portion:
            raise ObjectDoesNotExist()

        old_calories = recipe_calculate_calories_based_on_portion(
            recipe_portion.portion, recipe_portion.recipe)
        recipe_portion.meal.calories -= old_calories

        setattr(recipe_portion, 'portion', dto.portion)
        recipe_portion.save()

        dto = RecalculateMealCaloriesDto(
            recipes=[{'recipe': recipe_portion.recipe.id,
                      'portion': recipe_portion.portion}]
        )
        RecalculateMealCalories().add_recipes(dto, recipe_portion.meal)


@dataclass
class UpdateMealIngredientDto:
    unit: int
    amount: int


class UpdateMealIngredient:
    def update(self, meal_ingredient: Meal, dto: UpdateMealIngredientDto) -> None:
        meal_ingredient.meal.calories -= self._calculate_calories_to_be_substracted(
            meal_ingredient)

        if meal_ingredient.unit_id != dto.unit:
            if not unit_list().filter(id=dto.unit).exists():
                raise ValidationError(
                    f'Unit with id {dto.unit} does not exists')
            meal_ingredient.unit_id = dto.unit
        meal_ingredient.amount = dto.amount
        dto = RecalculateMealCaloriesDto(
            ingredients=[{'ingredient': meal_ingredient.ingredient,
                          'unit': dto.unit, 'amount': dto.amount}]
        )
        RecalculateMealCalories().add_ingredients(dto, meal_ingredient.meal)

    @staticmethod
    def _calculate_calories_to_be_substracted(ing: IngredientAmount) -> int:
        return ingredient_calculate_calories(
            ingredient=ing.ingredient,
            unit=ing.unit,
            amount=ing.amount
        )


class DeleteMeal:
    def delete(self, meal: Meal) -> None:
        meal.delete()
