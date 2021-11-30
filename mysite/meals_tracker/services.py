from dataclasses import dataclass
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
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
        recipes_dto = AddRecipesToMealDto(
            user=meal.user, recipes=dto.recipes)
        AddRecipesToMeal().add(meal, recipes_dto)

        ingredients_dto = AddIngredientsToMealDto(
            user=meal.user, ingredients=dto.ingredients)
        AddIngredientsToMeal().add(meal, ingredients_dto)

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


@dataclass
class DeleteRecipeFromMealDto:
    recipe: int


class DeleteRecipeFromMeal:
    def delete(self, meal: Meal, dto: DeleteRecipeFromMealDto) -> None:
        meal.recipes.remove(dto.recipe)


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


@dataclass
class DeleteIngredientFromMealDto:
    ingredient: int


class DeleteIngredientFromMeal:
    def delete(self, meal: Meal, dto: DeleteIngredientFromMealDto) -> None:
        meal.ingredients.remove(dto.ingredient)


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
        if dto.recipes:
            recipes_ids = [item['recipe'] for item in dto.recipes]
            recipes_to_be_added = Recipe.objects.filter(id__in=recipes_ids)
            for recipe, item in zip(recipes_to_be_added, dto.recipes):
                meal.calories += recipe_calculate_calories_based_on_portion(
                    item['portion'], recipe)

    def add_ingredients(self, dto: RecalculateMealCaloriesDto, meal: Meal) -> None:
        if not dto.ingredients:
            return
        ingredients_ids = [item['ingredient']
                           for item in dto.ingredients]
        unit_ids = [item['unit'] for item in dto.ingredients]
        ingredients_with_amount = Ingredient_Unit.objects.filter(
            ingredient_id__in=ingredients_ids, unit_id__in=unit_ids).prefetch_related('ingredient', 'unit')
        for item, dto_item in zip(ingredients_with_amount, dto.ingredients):
            meal.calories += ingredient_calculate_calories(
                item.ingredient, item.unit, dto_item['amount'])


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
    recipe: int
    portion: int

    def __post_init__(self):
        if self.portion < 1:
            raise ValidationError(f'Incorrect portion: {self.portion}')


class UpdateMealRecipe:
    def update(self, meal: Meal, dto: UpdateMealRecipeDto) -> None:
        try:
            recipe_to_be_updated = meal.recipe_portion.get(
                recipe_id=dto.recipe)
        except RecipePortion.DoesNotExist:
            raise ValidationError(
                f'No recipe with id {dto.recipe} added to meal id {meal.id}')
        setattr(recipe_to_be_updated, 'portion', dto.portion)


@dataclass
class UpdateMealIngredientDto:
    ingredient: int
    unit: int
    amount: int


class UpdateMealIngredient:
    def update(self, meal: Meal, dto: UpdateMealIngredientDto) -> None:

        ingredient_amount = self._get_ingredient_amount_object(dto.ingredient)

        meal.calories -= self._calculate_calories_to_be_substracted(
            ingredient_amount)

        if ingredient_amount.unit_id != dto.unit:
            if not unit_list().filter(id=dto.unit).exists():
                raise ValidationError(
                    f'Unit with id {dto.unit} does not exists')
            ingredient_amount.unit_id = dto.unit
        ingredient_amount.amount = dto.amount
        dto = RecalculateMealCaloriesDto(
            ingredients=[{'ingredient': dto.ingredient,
                          'unit': dto.unit, 'amount': dto.amount}]
        )
        RecalculateMealCalories().add_ingredients(dto, meal)

    @staticmethod
    def _get_ingredient_amount_object(id: int) -> IngredientAmount:
        try:
            return IngredientAmount.objects.get(
                ingredient_id=id)
        except IngredientAmount.DoesNotExist:
            raise ValidationError(
                f'Ingredient with id {id} does not exists')

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
