from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from meals_tracker.models import Meal, MealCategory, RecipePortion, IngredientAmount
from recipe import selectors as recipe_selectors
from recipe.models import Recipe, Ingredient, Unit
from dataclasses import dataclass
from typing import List, Dict
from abc import ABC, abstractmethod


@dataclass
class BaseService(ABC):
    data: List[Dict]

    @abstractmethod
    def validate(self):
        pass


@dataclass
class MainService(ABC):

    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def update(self):
        pass


@dataclass
class M2MHandler(ABC):
    """ Base class for m2m handlers """

    @abstractmethod
    def pop_m2m_fields(self) -> dict:
        pass

    @abstractmethod
    def save_m2m_fields(self) -> None:
        pass

    @abstractmethod
    def _clear_m2m_relation(self) -> None:
        pass


class MealM2MHandler(M2MHandler):
    """ m2m handler for meal """

    def pop_m2m_fields(self) -> None:
        """ pop m2m meal fields and set as class attribute """
        if 'recipes' in self.data:
            self.recipes = RecipePortionService(
                user=self.user, data=self.data.pop('recipes'))
        if 'ingredients' in self.data:
            self.ingredients = IngredientAmountService(
                user=self.user, data=self.data.pop('ingredients'))

    def save_m2m_fields(self) -> None:
        """ save meal m2m fields """
        if self.recipes:
            for item in self.recipes.data:
                self.instance.recipes.add(item['recipe'], through_defaults={
                                                  'portion': item['portion']})
        if self.ingredients:
            for item in self.ingredients.data:
                self.instance.ingredients.add(item['ingredient'], through_defaults={
                                 'unit': item['unit'], 'amount': item['amount']})

    def _clear_m2m_relation(self) -> None:
        self.instance.recipes.clear()
        self.instance.ingredients.clear()


@dataclass
class RecipePortionService(BaseService):
    user: get_user_model
    data: List[Dict[str, int]]

    def validate(self):
        """ validate if given ids exists in db """
        available_recipes = recipe_selectors.recipe_list(self.user)

        for item in self.data:
            try:
                id = item['recipe']
                item['recipe'] = available_recipes.get(id=id)
            except Recipe.DoesNotExist:
                raise ObjectDoesNotExist(
                    f'Recipe with id {id} does not exists')


@dataclass
class IngredientAmountService(BaseService):
    user: get_user_model
    data: List[Dict[str, int]]

    def validate(self):
        all_ingredients = recipe_selectors.ingredient_list()
        all_units = recipe_selectors.unit_list()
        for item in self.data:
            try:
                ingredient_id = item['ingredient']
                unit_id = item['unit']
                item['ingredient'] = all_ingredients.get(id=ingredient_id)
                item['unit'] = all_units.get(id=unit_id)
            except Ingredient.DoesNotExist:
                raise ObjectDoesNotExist(
                    f'Ingredient with id {ingredient_id} does not exists!')
            except Unit.DoesNotExist:
                raise ObjectDoesNotExist(
                    f'unit with id {unit_id} does not exists!')


@dataclass
class MealService(MainService, MealM2MHandler):

    user: get_user_model
    data: dict
    recipes: RecipePortionService = None
    ingredients: IngredientAmountService = None
    kwargs: dict = None

    def create(self):
        """ create meal """
        self.instance = Meal.objects.create(
            user=self.user, category=self.category)
        self.save_m2m_fields()
        return self.instance

    def update(self):
        """ update meal """
        if not self.partial:
            self._clear_m2m_relation()
        if self.category:
            self.instance.category = self.category
        self.save_m2m_fields()
        self.instance.save()

    def validate(self):
        """ validate data """
        if self.category:
            try:
                self.category = MealCategory.objects.get(id=self.category)
            except MealCategory.DoesNotExist:
                raise ObjectDoesNotExist(
                    f'No category with such id {self.category}')

        if self.recipes:
            self.recipes.validate()
        if self.ingredients:
            self.ingredients.validate()

    @staticmethod
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
            obj = IngredientAmount.objects.get(
                ingredient=ingredient, meal=meal)
            meal.calories += recipe_selectors.ingredient_calculate_calories(ingredient=ingredient,
                                                                            unit=obj.unit, amount=obj.amount)
        meal.save()

    def __post_init__(self):
        self.pop_m2m_fields()
        if 'category' in self.data:
            self.category = self.data.pop('category')
        else:
            self.category = None
        if self.kwargs:
            self.partial = self.kwargs.get('partial')
            self.instance = self.kwargs.get('instance')
        self.validate()
