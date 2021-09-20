from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from meals_tracker.models import Meal, MealCategory, RecipePortion, IngredientAmount
from recipe import selectors as recipe_selectors
from recipe.models import Recipe, Ingredient, Unit
from dataclasses import dataclass
from typing import List
from abc import ABC, abstractmethod


@dataclass
class BaseDataClass(ABC):

    @abstractmethod
    def validate(self) -> None:
        pass


@dataclass
class CategoryDataclass(BaseDataClass):
    category: int

    def validate(self) -> bool:
        """ check if category has mapping in db """

        try:
            self.category = MealCategory.objects.get(id=self.category)
        except MealCategory.DoesNotExist:
            raise ObjectDoesNotExist(
                f'No category with such id {self.category}')

    def check_is_category_is_not_null(self) -> None:
        """ check if category is set otherwise raise error """
        if self.category is None:
            raise ValidationError('Category has to be set')


@dataclass
class RecipeDataClass(BaseDataClass):
    recipe: int
    portion: int

    def validate(self, user) -> bool:
        """ check if recipe is avilable for given user """
        try:
            available_recipes = recipe_selectors.get_recipes(user)
            available_recipes.get(id=self.recipe)
        except Recipe.DoesNotExist:
            raise ObjectDoesNotExist(f'No recipe with such id {self.recipe}')


@dataclass
class IngredientDataClass(BaseDataClass):
    ingredient: int
    unit: int
    amount: int

    def validate(self) -> bool:
        """ check if ingredient is availabe for given user """
        try:
            self.ingredient = Ingredient.objects.get(id=self.ingredient)
        except Ingredient.DoesNotExist:
            raise ObjectDoesNotExist(
                f'No ingredient with such id {self.ingredient}')
        try:
            self.unit = Unit.objects.get(id=self.unit)
        except Unit.DoesNotExist:
            raise ObjectDoesNotExist(f'No unit with such id {self.unit}')


@dataclass
class MealDataClass:
    category: CategoryDataclass = None
    recipes: List[RecipeDataClass] = None
    ingredients: List[IngredientDataClass] = None

    def create(self, user: get_user_model) -> Meal:
        """ create meal """
        instance = Meal.objects.create(
            user=user, category=self.category.category)
        if self.recipes:
            for item in self.recipes:
                instance.recipes.add(item.recipe, through_defaults={
                                    'portion': item.portion})
        if self.ingredients:
            for item in self.ingredients:
                instance.ingredients.add(item.ingredient, through_defaults={
                                 'unit': item.unit, 'amount': item.amount})
        return instance

    def update(self, instance: Meal) -> Meal:
        """ update meal """
        if self.category:
            instance.category = self.category.category
        if self.recipes:
            for item in self.recipes:
                instance.recipes.add(item.recipe, through_defaults={
                                    'portion': item.portion})
        if self.ingredients:
            for item in self.ingredients:
                instance.ingredients.add(item.ingredient, through_defaults={
                                 'unit': item.unit, 'amount': item.amount})

        return instance


@dataclass
class MealManyToManyHandler:
    recipes: list = None
    ingredients: list = None

    def get_recipes(self, user: get_user_model) -> list[Recipe]:
        """ get and validate recipes from raw data """
        recipes = []
        if self.recipes:
            for item in self.recipes:
                recipe = RecipeDataClass(
                    *[values for values in list(item.values())])
                recipe.validate(user=user)
                recipes.append(recipe)
        return recipes

    def get_ingredients(self):
        """ get and validate ingredients from raw data """
        ingredients = []
        if self.ingredients:
            for item in self.ingredients:
                ingredient = IngredientDataClass(
                    *[values for values in list(item.values())])
                ingredient.validate()
                ingredients.append(ingredient)
        return ingredients


def meal_post_handler(user: get_user_model, data: dict) -> Meal:
    """ meal post action handler """

    ingredients = data.get('ingredients')
    recipes = data.get('recipes')

    category = CategoryDataclass(category=data.get('category'))
    category.check_is_category_is_not_null()
    category.validate()
    meal = MealDataClass(category)

    m2m_handler = MealManyToManyHandler(recipes, ingredients)

    meal.recipes = m2m_handler.get_recipes(user=user)
    meal.ingredients = m2m_handler.get_ingredients()

    meal_instance = meal.create(user=user)
    meal_instance.save()
    return meal_instance


def meal_put_handler(instance: Meal, data: dict) -> Meal:
    """ handling put request """

    category = CategoryDataclass(category=data.get('category'))
    category.check_is_category_is_not_null()
    category.validate()
    clear_m2m_relation(instance)
    meal = MealDataClass(category)
    return meal_update_handler(instance, meal, data)


def meal_patch_handler(instance: Meal, data: dict) -> Meal:
    """ meal update handler """
    category = CategoryDataclass(category=instance.category)
    meal = MealDataClass(category)
    return meal_update_handler(instance, meal, data)


def meal_update_handler(instance: get_user_model, meal: MealDataClass, data: dict) -> Meal:
    """ handling pure update operation """

    ingredients = data.get('ingredients')
    recipes = data.get('recipes')

    m2m_handler = MealManyToManyHandler(recipes, ingredients)
    meal.recipes = m2m_handler.get_recipes(user=instance.user)
    meal.ingredients = m2m_handler.get_ingredients()

    instance = meal.update(instance=instance)
    instance.save()
    return instance


def meal_put_handler(instance: Meal, data: dict) -> Meal:
    """ meal put action handler """

    clear_m2m_relation(instance)

    ingredients = data.get('ingredients')
    recipes = data.get('recipes')

    category = CategoryDataclass(category=data.get('category'))
    category.validate()
    meal = MealDataClass(category)

    m2m_handler = MealManyToManyHandler(recipes, ingredients)
    meal.recipes = m2m_handler.get_recipes(user=instance.user)
    meal.ingredients = m2m_handler.get_ingredients()

    instance = meal.update(instance=instance)
    instance.save()
    return instance


def clear_m2m_relation(instance: Meal) -> None:
    """ clear m2m realtions when request action == put """
    instance.recipes.clear()
    instance.ingredients.clear()


def pop_m2m_fields(instance, user: get_user_model, data: dict) -> dict:
    """ pop m2m fields """

    if isinstance == Meal:
        return pop_meal_m2m_fields(user, data)


def pop_meal_m2m_fields(user: get_user_model, data: dict) -> dict:
    """ pop m2m fields specific for Meal """
    return_dict = {'recipes': [], 'ingredients': []}
    if 'recipes' in data:
        pass
    if 'ingredients' in data:
        pass


def recalculate_total_meal_calories(meal: Meal) -> None:
    """ recalculate total meal calories based on added recipes,
    ingredients and ready meals """
    meal.calories = 0
    for recipe in meal.recipes.all():
        obj = RecipePortion.objects.get(recipe=recipe, meal=meal)
        if recipe.calories is not None:
            meal.calories += recipe_selectors.recipe_calculate_calories_based_on_portion(
                obj.portion, recipe)
    for ingredient in meal.ingredients.all():
        obj = IngredientAmount.objects.get(ingredient=ingredient, meal=meal)
        meal.calories += recipe_selectors.ingredient_calculate_calories(ingredient=ingredient,
                                                                        unit=obj.unit, amount=obj.amount)
    meal.save()
    meal.save()
