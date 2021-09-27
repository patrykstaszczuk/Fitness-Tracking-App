from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.text import slugify
from django.db.utils import IntegrityError
from unidecode import unidecode
from django.core.exceptions import ValidationError

from typing import Optional
from recipe.models import Recipe, Tag, Ingredient, Recipe_Ingredient, Unit, Ingredient_Unit
from recipe import selectors
import os
import shutil
from dataclasses import dataclass
from abc import ABC, abstractmethod


class Dish(ABC):
    """ base class for dishes """
    @abstractmethod
    def _set_slug(self, instance):
        """ set appropriate slug for instance """
        pass

    @abstractmethod
    def _validate(self):
        """ perform validation """
        pass

    @abstractmethod
    def create(self):
        """ create instance """
        pass

    @abstractmethod
    def update(self):
        """ update instance """
        pass

    @abstractmethod
    def delete(instance):
        """ delete instance """
        pass


class M2MHandler(ABC):
    """ base class for m2m handlers """

    @abstractmethod
    def pop_m2m_fields(self) -> dict:
        """ pop m2m fields from incoming data and set it as class attributes """
        pass

    @abstractmethod
    def save_m2m_fields(self) -> None:
        """ save m2m fields into instance """
        pass

    @abstractmethod
    def _clear_m2m_relation() -> None:
        """ clear all m2m instance relations """
        pass


class Validator(ABC):
    """ base class for different validation types """

    @abstractmethod
    def validate(self):
        """ perfom validation """

    # @abstractmethod
    # def create_validation(self):
    #     """ perform validation during create """
    #     pass
    #
    # @abstractmethod
    # def update_validation(self):
    #     """ perform validation during update """
    #     pass

@dataclass
class IngredientUnitValidator(Validator):
    """ validate ingredient """
    ingredients: list[dict]

    def validate(self) -> list[dict]:
        """ check if ingredients are available to user """
        ingredient_slugs = []
        unit_ids = []
        for item in self.ingredients or []:
            ingredient_slugs.append(item['ingredient'])
            unit_ids.append(item['unit'])
        ingredient_instances = selectors.ingredient_get_multi_by_slugs(
            ingredient_slugs)
        unit_instances = selectors.unit_get_multi_by_ids(unit_ids)
        for item, instance, unit in zip(self.ingredients, ingredient_instances, unit_instances):
            item['ingredient'] = instance
            item['unit'] = unit
        return self.ingredients


@dataclass
class TagValidator(Validator):
    """ validate tag """
    tags: list[str]
    user: get_user_model

    def validate(self) -> list[Tag]:
        """ check if tag is available for user """
        return selectors.tag_get_multi_by_slugs(
            user=self.user, slugs=self.tags)

# class RecipeValidator(Validator):
#
#     def create_validation(self):
#         """ perform validation during create """
#         if hasattr(self, 'tags'):
#             self.tags = selectors.tag_get_multi_by_slugs(
#                 user=self.user, slugs=self.tags)
#         if hasattr(self, 'ingredients'):
#             ingredient_slugs = []
#             unit_ids = []
#             for item in self.ingredients or []:
#                 ingredient_slugs.append(item['ingredient'])
#                 unit_ids.append(item['unit'])
#             ingredient_instances = selectors.ingredient_get_multi_by_slugs(
#                 ingredient_slugs)
#             unit_instances = selectors.unit_get_multi_by_ids(unit_ids)
#             for item, instance, unit in zip(self.ingredients, ingredient_instances, unit_instances):
#                 item['ingredient'] = instance
#                 item['unit'] = unit
#
#     def update_validation(self):
#         """ perform validation during update """
#         pass


class RecipeM2MHandler(M2MHandler):
    """ recipe m2m handler """

    def pop_m2m_fields(self) -> dict:
        for field in Recipe._meta.many_to_many:
            if self.data.get(field.name) is not None:
                setattr(self, field.name, self.data.pop(field.name))
        return self.data

    def save_m2m_fields(self) -> None:
        if hasattr(self, 'tags'):
            self.instance.tags.set(self.tags)
        if hasattr(self, 'ingredients'):
            for item in self.ingredients:
                ingredient = item.pop('ingredient')
                item.update({'recipe': self.instance})
                self.instance.ingredients.add(
                    ingredient, through_defaults={**item})

    def _clear_m2m_relation(self) -> None:
        self.instance.tags.clear()
        self.instance.ingredients.clear()


@dataclass
class RecipeService(Dish, RecipeM2MHandler):
    user: get_user_model
    data: dict
    kwargs: Optional[dict] = None

    def create(self):
        """ create recipe based on parameters """

        self._validate()
        self.instance = Recipe(user=self.user, **self.data)
        self.instance.slug = self._set_slug(self.data['name'])
        self.instance.save()
        self.save_m2m_fields()
        return self.instance

    def update(self) -> Recipe:
        """ update instance """
        self._validate()
        for attr in self.data:
            setattr(self.instance, attr, self.data[attr])
        if self._check_if_name_exists(self.instance.name).exclude(id=self.instance.id).count() > 0:
            raise ValidationError(
                f'You already have reciep with name {self.instance.name}')
        if not self.partial:
            self._clear_m2m_relation()
        self.instance.slug = self._set_slug(self.instance.name)
        self.save_m2m_fields()
        self.instance.save()
        return self.instance

    def _set_slug(self, name: str) -> str:
        """ set proper slug """
        slug = slugify(name)
        number_of_repeared_names = self._check_if_name_exists(name).count()
        if number_of_repeared_names > 0:
            slug += str(number_of_repeared_names + 1)
        return slug

    def _check_if_name_exists(self, name: str) -> list[Recipe]:
        """ return number of recipes with same name and user """
        return Recipe.objects.filter(user=self.user, name=name)

    def _validate(self):
        if hasattr(self, 'tags'):
            validator = TagValidator(tags=self.tags, user=self.user)
            self.tags = validator.validate()
        if hasattr(self, 'ingredients'):
            validator = IngredientUnitValidator(self.ingredients)
            self.ingredients = validator.validate()
    # def _validate(self):
    #     """ validate data """
    #     if hasattr(self, 'tags'):
    #         self.tags = selectors.tag_get_multi_by_slugs(
    #             user=self.user, slugs=self.tags)
    #
    #     if hasattr(self, 'ingredients'):
    #         ingredient_slugs = []
    #         unit_ids = []
    #         for item in self.ingredients or []:
    #             ingredient_slugs.append(item['ingredient'])
    #             unit_ids.append(item['unit'])
    #         ingredient_instances = selectors.ingredient_get_multi_by_slugs(
    #             ingredient_slugs)
    #         unit_instances = selectors.unit_get_multi_by_ids(unit_ids)
    #         for item, instance, unit in zip(self.ingredients, ingredient_instances, unit_instances):
    #             item['ingredient'] = instance
    #             item['unit'] = unit

    @staticmethod
    def recalculate_nutritions_values(recipe: Recipe) -> None:
        """ recalculating recipe nutritions values based on ingredients """
        nutritional_fields = ['proteins', 'carbohydrates', 'fats', 'calories']
        for field in nutritional_fields:
            setattr(recipe, field, 0)

        recipe_ingredients = recipe.ingredients.all()
        for ingredient in recipe_ingredients:
            obj = ingredient.recipe_ingredient_set.get(
                recipe=recipe, ingredient=ingredient)
            unit = obj.unit
            amount = obj.amount
            if not all([unit, amount]):
                continue

            for field in nutritional_fields:
                current_recipe_field_value = getattr(recipe, field)
                ingredient_field_value = getattr(ingredient, field)
                if ingredient_field_value is None:
                    ingredient_field_value = 0
                grams = selectors.ingredient_convert_unit_to_grams(
                    ingredient, unit, amount)
                setattr(recipe, field, round((current_recipe_field_value
                                              + (grams/100)*ingredient_field_value), 2))
        kwargs = {'force_insert': False}
        recipe.save(**kwargs, update_fields=['proteins', 'carbohydrates',
                                             'fats', 'calories'])

    @staticmethod
    def delete(recipe: Recipe) -> None:
        """ delete recipe """
        if recipe:
            recipe.delete()

    def __post_init__(self):
        self.data = self.pop_m2m_fields()
        if self.kwargs:
            self.partial = self.kwargs.get('partial')
            self.instance = self.kwargs.get('instance')


@dataclass
class TagService(Dish):
    """ Tag services """
    user: get_user_model
    data: dict

    def create(self) -> Tag:
        """ create new tag """
        self._validate()
        name = self.data['name']
        tag = Tag.objects.create(user=self.user, name=name)
        tag.slug = self._set_slug(name)
        tag.save()
        return tag

    def update(self, instance: Tag) -> Tag:
        """ update Tag instance """
        self._validate_update(instance)

        for attr in self.data:
            setattr(instance, attr, self.data[attr])
        instance.save()
        return instance

    def _set_slug(self, name: str) -> str:
        return slugify(name)

    def _check_if_name_exists(self, name: str) -> list[Tag]:
        """ return number of tags with same name and user """
        return Tag.objects.filter(user=self.user, name=name)

    def _validate(self) -> None:
        """ check if tag name alredy exists """
        name = self.data['name']
        if self._check_if_name_exists(name).count() > 0:
            raise ValidationError(
                f'Tag with name {name} already exists!')

    def _validate_update(self, tag: Tag) -> None:
        """ check if new name exisis in db """
        name = self.data['name']
        if self._check_if_name_exists(name).exclude(id=tag.id).count() > 0:
            raise ValidationError(f'Tag with name {name} already exists!')

    @staticmethod
    def delete(tag: Tag) -> None:
        """ delete tag """
        if tag:
            tag.delete()


class IngredientM2MHandler(M2MHandler):
    """ ingredient m2m handler """

    def pop_m2m_fields(self) -> dict:
        """ pop ingredient m2m fields """
        for field in Ingredient._meta.many_to_many:
            if self.data.get(field.name) is not None:
                setattr(self, field.name, self.data.pop(field.name))
        return self.data

    def save_m2m_fields(self) -> None:
        """ save ingredient m2m fields """
        if hasattr(self, 'tags'):
            self.instance.tags.add(*self.tags)
        if hasattr(self, 'units'):
            for item in self.units:
                self.instance.units.add(item['unit'], through_defaults={
                                     'grams_in_one_unit': item['grams_in_one_unit']})

    def _clear_m2m_relation(self) -> None:
        """ clear m2m relation during PUT request """
        self.instance.tags.clear()
        self.instance.units.clear()


@dataclass()
class IngredientService(Dish, IngredientM2MHandler):
    user: get_user_model
    data: dict
    kwargs: Optional[dict] = None

    def create(self) -> Ingredient:
        """ create ingredient """
        self._validate()
        if hasattr(self, 'ready_meal') and self.ready_meal:
            self._handle_ready_meal()
        self.instance = Ingredient.objects.create(user=self.user, **self.data)
        self.instance.slug = self._set_slug(self.instance)
        self.instance.save()
        self._set_default_unit(self.instance)
        self.save_m2m_fields()
        return self.instance

    def update(self) -> Ingredient:
        """ update instance """
        self._validate()
        for attr in self.data:
            setattr(self.instance, attr, self.data[attr])
        if 'name' in self.data:
            self.instance.slug = self._set_slug(self.instance)
        if not self.partial:
            self._clear_m2m_relation()
        self.save_m2m_fields()
        self.instance.save()
        return self.instance

    def _check_if_name_exists(self, name: str) -> list[Tag]:
        """ return number of tags with same name and user """
        return Tag.objects.filter(user=self.user, name=name)

    def _validate(self) -> bool:
        """ overall validation """
        name = self.data.get('name')
        if self._check_if_name_exists(name).count() > 0:
            raise ValidationError(
                f'You alredy have ingredient with name {name}!')
        if hasattr(self, 'tags'):
            self.tags = selectors.tag_get_multi_by_slugs(self.user, self.tags)
        if hasattr(self, 'units'):
            unit_ids = []
            for item in self.units:
                unit_ids.append(item['unit'])
            unit_instances = selectors.unit_get_multi_by_ids(ids=unit_ids)
            for item, unit in zip(self.units, unit_instances):
                item['unit'] = unit

    def _validate_update(self):
        """ overall validation during update """

    def _set_slug(self, instance: Ingredient) -> str:
        """ set appropriate slug """
        slug = slugify(unidecode(instance.name)) + \
            '-user-' + str(instance.user.id)
        number_of_repeared_names = self._check_if_name_exists(instance).count()
        if number_of_repeared_names > 0:
            slug += str(number_of_repeared_names + 1)
        return slug

    def _check_if_name_exists(self, name: str) -> list[Ingredient]:
        """ return number of ingredients with same name and user """
        return Ingredient.objects.filter(user=self.user, name=name)

    def _handle_ready_meal(self) -> bool:
        """ append ready_meal tag to ingredient service tags """
        ready_meal_tag = selectors.tag_ready_meal_get_or_create(user=self.user)
        if hasattr(self, 'tags'):
            self.tags.append(ready_meal_tag[0])
        else:
            self.tags = [ready_meal_tag[0]]

    @staticmethod
    def _set_default_unit(ingredient: Ingredient) -> None:
        """ set default unit to new ingredient """
        gram_unit_instance, created = selectors.unit_get(id=None, default=True)
        ingredient.units.add(gram_unit_instance, through_defaults={
                             'grams_in_one_unit': 100})

    @staticmethod
    def delete(ingredient: Ingredient) -> None:
        """ delete ingredient """
        ingredient.delete()

    def __post_init__(self):
        self.data = self.pop_m2m_fields()
        if self.data.get('ready_meal'):
            self.ready_meal = self.data.pop('ready_meal')
        if self.kwargs:
            self.partial = self.kwargs.get('partial')
            self.instance = self.kwargs.get('instance')


#
# def recipe_upload_file(recipe: Recipe, data: dict) -> None:
#     """ upload file for recipe """
#     for item in data:
#         setattr(recipe, item, data[item])
#     recipe.save()
#
#


#
# def recalculate_nutritions_values(recipe: Recipe) -> None:
#     """ recalculating recipe nutritions values based on ingredients """
#     nutritional_fields = ['proteins', 'carbohydrates', 'fats', 'calories']
#     for field in nutritional_fields:
#         setattr(recipe, field, 0)
#
#     for ingredient in recipe.ingredients.all():
#         obj = Recipe_Ingredient.objects.get(recipe=recipe,
#                                             ingredient=ingredient)
#         unit = obj.unit
#         amount = obj.amount
#         if not all([unit, amount]):
#             continue
#
#         for field in nutritional_fields:
#             current_recipe_field_value = getattr(recipe, field)
#             ingredient_field_value = getattr(ingredient, field)
#             if ingredient_field_value is None:
#                 ingredient_field_value = 0
#             grams = selectors.ingredient_convert_unit_to_grams(
#                 ingredient, unit, amount)
#             setattr(recipe, field, round((current_recipe_field_value
#                                           + (grams/100)*ingredient_field_value), 2))
#     kwargs = {'force_insert': False}
#     recipe.save(**kwargs, update_fields=['proteins', 'carbohydrates',
#                                          'fats', 'calories'])
#     recipe.save(**kwargs, update_fields=['proteins', 'carbohydrates',
#                                          'fats', 'calories'])
