from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.text import slugify
from django.db.utils import IntegrityError
from unidecode import unidecode
from django.core.exceptions import ValidationError

from typing import Iterable, Union
from recipe.models import Recipe, Tag, Ingredient, Recipe_Ingredient, Unit, Ingredient_Unit
from recipe import selectors
import os
import shutil
from dataclasses import dataclass
from abc import ABC, abstractmethod


class Dish(ABC):

    @abstractmethod
    def _set_slug(self, instance):
        pass

    @abstractmethod
    def _validate(self):
        pass

    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def update(self):
        pass


class M2MHandler(ABC):
    """ abstrack class for m2m handlers """

    @abstractmethod
    def pop_m2m_fields(self, data: dict) -> dict:
        pass

    @abstractmethod
    def save_m2m_fields(self, instance: Union[Recipe, Ingredient]) -> None:
        pass

    @abstractmethod
    def _clear_m2m_relation() -> None:
        pass


class RecipeM2MHandler(M2MHandler):
    """ recipe m2m handler """

    def pop_m2m_fields(self, data) -> dict:
        """ pop recipe m2m fields """
        for field in Recipe._meta.many_to_many:
            if data.get(field.name) is not None:
                setattr(self, field.name, data.pop(field.name))
        return data

    def save_m2m_fields(self, recipe: Recipe) -> None:
        """ save recipe m2m fields """
        recipe.tags.set(self.tags)
        if self.ingredients:
            for item in self.ingredients:
                ingredient = item.pop('ingredient')
                item.update({'recipe': recipe})
                recipe.ingredients.add(ingredient, through_defaults={**item})

    def _clear_m2m_relation(instance: Recipe) -> bool:
        pass


@dataclass(init=False)
class RecipeService(Dish, RecipeM2MHandler):
    user: get_user_model
    data: dict = None
    tags: list[Tag]
    ingredients: list[Recipe_Ingredient] = None

    def create(self):
        """ create recipe based on parameters """
        self._validate()
        recipe = Recipe(user=self.user, **self.data)
        recipe.slug = self._set_slug(recipe)
        recipe.save()
        self.save_m2m_fields(recipe)
        return recipe

    def update(self):
        pass

    def _set_slug(self, recipe: Recipe) -> str:
        """ set proper slug """
        name = self.data['name']
        slug = slugify(name)
        number_of_repeared_names = self._check_if_name_exists(name).count()
        if number_of_repeared_names > 0:
            slug += str(number_of_repeared_names + 1)
        return slug

    def _check_if_name_exists(self, name: str) -> list[Recipe]:
        """ return number of recipes with same name and user """
        return Recipe.objects.filter(user=self.user, name=name)

    def _validate(self):
        """ validate data """
        if self.tags:
            self.tags = selectors.tag_get_multi_by_slugs(
                user=self.user, slugs=self.tags)

        if self.ingredients:
            ingredient_slugs = []
            for item in self.ingredients:
                ingredient_slugs.append(item['ingredient'])
            ingredient_instances = selectors.ingredient_get_multi_by_slugs(
                ingredient_slugs)
            for item, instance in zip(self.ingredients, ingredient_instances):
                item['ingredient'] = instance

    def __init__(self, user, data):
        self.user = user
        self.data = self.pop_m2m_fields(data)


@dataclass
class TagService(Dish):
    """ Tag services """
    user: get_user_model
    data: dict

    def create(self) -> Tag:
        """ create new tag """
        self._validate()
        tag = Tag.objects.create(user=self.user, name=self.data['name'])
        tag.slug = self._set_slug()
        tag.save()
        return tag

    def update(self, instance: Tag) -> Tag:
        """ update Tag instance """
        self._validate_update(instance)

        for attr in self.data:
            setattr(instance, attr, self.data[attr])
        instance.save()
        return instance

    def _set_slug(self) -> str:
        return slugify(self.data['name'])

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


class IngredientM2MHandler(M2MHandler):
    """ ingredient m2m handler """

    def pop_m2m_fields(self, data) -> dict:
        """ pop ingredient m2m fields """
        for field in Ingredient._meta.many_to_many:
            if data.get(field.name) is not None:
                setattr(self, field.name, data.pop(field.name))
        return data

    def save_m2m_fields(self, ingredient: Ingredient) -> None:
        """ save ingredient m2m fields """
        if self.tags:
            ingredient.tags.add(*self.tags)
        if self.units:
            for item in self.units:
                ingredient.units.add(item['unit'], through_defaults={
                                     'grams_in_one_unit': item['grams_in_one_unit']})

    @staticmethod
    def _clear_m2m_relation(instance: Ingredient) -> None:
        """ clear m2m relation during PUT request """
        instance.tags.clear()
        instance.units.clear()


@dataclass(init=False)
class IngredientService(Dish, IngredientM2MHandler):
    user: get_user_model
    data: dict
    ready_meal: bool = False
    units: list[Ingredient_Unit] = None
    tags: list[Tag] = None

    def create(self) -> Ingredient:
        """ create ingredient """
        self._validate()
        if self.ready_meal:
            self._handle_ready_meal()
        ingredient = Ingredient.objects.create(user=self.user, **self.data)
        ingredient.slug = self._set_slug(ingredient)
        ingredient.save()
        self._set_default_unit(ingredient)
        self.save_m2m_fields(ingredient)
        return ingredient

    def update(self, ingredient: Ingredient, partial: bool) -> Ingredient:
        """ update ingredient """
        self._validate()
        for attr in self.data:
            setattr(ingredient, attr, self.data[attr])
        if 'name' in self.data:
            ingredient.slug = self._set_slug(ingredient)
        if not partial:
            self._clear_m2m_relation(ingredient)
        self.save_m2m_fields(ingredient)
        ingredient.save()
        return ingredient

    def _check_if_name_exists(self, name: str) -> list[Tag]:
        """ return number of tags with same name and user """
        return Tag.objects.filter(user=self.user, name=name)

    def _validate(self) -> bool:
        """ overall validation """
        name = self.data.get('name')
        if self._check_if_name_exists(name).count() > 0:
            raise ValidationError(
                f'You alredy have ingredient with name {name}!')
        if self.tags:
            self.tags = selectors.tag_get_multi_by_slugs(self.user, self.tags)
        if self.units:
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
        if self.tags is not None:
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

    def __init__(self, user, data):
        self.user = user
        if data.get('ready_meal'):
            self.ready_meal = data.pop('ready_meal')
        self.data = self.pop_m2m_fields(data)


# def create_recipe(user: get_user_model, data: dict) -> Recipe:
#     """ create recipe based on user and data """
#
#     data_dict = pop_m2m_fields(
#         model=Recipe, user=user, data=data)
#     recipe = Recipe(user=user, **data)
#     recipe.slug = set_slug(recipe)
#     recipe.save()
#     data_dict.pop('data')
#     save_m2m_fields(recipe, data_dict)
#     return recipe
#
#
# def set_slug(instance: Union[Tag, Recipe]) -> str:
#     """ set recipe slug """
#
#     modified_name = ''
#
#     if isinstance(instance, Ingredient):
#         modified_name = slugify(unidecode(instance.name)) + \
#                                 '-user-' + str(instance.user.id)
#     else:
#         modified_name = instance.name
#
#     number_of_repeared_names = selectors.check_if_name_exists(instance)
#     if number_of_repeared_names > 0:
#         modified_name += str(number_of_repeared_names + 1)
#
#     slug = slugify(unidecode(modified_name))
#     return slug
#
#
# def update_recipe(recipe: Recipe, data: dict, method: str) -> Recipe:
#     """ update recipe based on user and data.
#      PUT request clears relational field before saving """
#     return object_update_with_m2m(recipe, data, method)
#
#
# def recipe_upload_file(recipe: Recipe, data: dict) -> None:
#     """ upload file for recipe """
#     for item in data:
#         setattr(recipe, item, data[item])
#     recipe.save()
#
#
# def clear_m2m_relation(instance):
#     """ clear m2m relation during PUT request """
#     if isinstance(instance, Recipe):
#         instance.tags.clear()
#         instance.ingredients.clear()
#         return None
#     if isinstance(instance, Ingredient):
#         instance.tags.clear()
#         instance.units.clear()
#         return None
#
#
# def pop_m2m_fields(model: Union[Recipe, Ingredient], user: get_user_model, data: dict) -> dict:
#     """ pop relational fields from data and return it """
#     if model == Ingredient:
#         return_dict = {'tags': [], 'units': []}
#         if 'tags' in data:
#             return_dict['tags'] = selectors.map_tags_slug_to_instances(
#                 user=user, tags_slug=data.pop('tags'))
#         if 'units' in data:
#             return_dict['units'] = data.pop('units')
#             for unit in return_dict['units']:
#                 unit['unit'] = selectors.unit_map_id_to_instance(unit['unit'])
#         return_dict.update({'data': data})
#         return return_dict
#     elif model == Recipe:
#         return_dict = {'tags': [], 'ingredients': []}
#         if 'tags' in data:
#             return_dict['tags'] = selectors.map_tags_slug_to_instances(
#                 user=user, tags_slug=data.pop('tags'))
#         if 'ingredients' in data:
#             return_dict['ingredients'] = selectors.map_data_to_instances(
#                 user=user, ingredients=data.pop('ingredients'))
#         return_dict.update({'data': data})
#         return return_dict
#
#
# def save_m2m_fields(obj: Union[Recipe, Ingredient], fields: dict) -> Recipe:
#     """ save m2m fields. m2m relations are not cleared when using PATCH """
#     if isinstance(obj, Recipe):
#         return save_recipe_m2m_fields(obj, fields)
#     if isinstance(obj, Ingredient):
#         return save_ingredient_m2m_fields(obj, fields)
#
#
# def save_recipe_m2m_fields(obj: Recipe, fields: list[Union[Tag, Ingredient]]) -> Recipe:
#     """ save m2m field for recipe """
#     tags = fields.get('tags')
#     ingredients = fields.get('ingredients')
#
#     if tags:
#         obj.tags.add(*(tags))
#     if ingredients:
#         for item in ingredients:
#             ingredient = item.pop('ingredient')
#             item.update({'recipe': obj})
#             obj.ingredients.add(ingredient, through_defaults={**item})
#     return obj
#
#
# def save_ingredient_m2m_fields(obj: Ingredient, fields: dict[list[Union[Tag, Unit]]]) -> Ingredient:
#     """ save m2m fiel for ingredinet """
#     tags = fields.get('tags')
#     units = fields.get('units')
#     if tags:
#         obj.tags.add(*(tags))
#     if units:
#         for item in units:
#             unit = item.pop('unit')
#             item.update({'ingredient': obj})
#             obj.units.add(unit, through_defaults={**item})
#     return obj
#
#
# def delete_recipe(instance: Recipe) -> None:
#     """ remove recipe from db """
#     path = str(settings.MEDIA_ROOT)
#     + "/recipes/" + instance.user.name + "/" + instance.slug
#     if os.path.exists(path):
#         shutil.rmtree(path)
#     instance.delete()
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
#
#
# def tag_create(user: get_user_model, data: dict) -> Tag:
#     """ create Tag """
#     data.update({'user': user})
#     try:
#         tag = Tag.objects.create(**data)
#     except IntegrityError:
#         raise ValidationError('Tag with provided name already exists!')
#     tag.slug = set_slug(tag)
#     tag.save()
#     return tag
#
#
# def tag_update(tag: Tag, data: dict) -> Tag:
#     """ update Tag """
#
#     for attr in data:
#         setattr(tag, attr, data[attr])
#     if 'name' in data:
#         tag.slug = set_slug(tag)
#     tag.save()
#     return tag
#
#
# def ingredient_create(user: get_user_model, data: dict) -> Ingredient:
#     """ create Ingredient """
#     ingredient_validate_input_data(data)
#     data_dict = pop_m2m_fields(model=Ingredient, user=user, data=data)
#     ingredient = Ingredient()
#     for attr, value in data_dict['data'].items():
#         setattr(ingredient, attr, value)
#     data_dict.pop('data')
#     ingredient.user = user
#     ingredient.slug = set_slug(ingredient)
#     try:
#         ingredient.save()
#     except IntegrityError:
#         raise ValidationError(
#             f'Ingredient with name "{ingredient.name}" for user id {user.id} already exsists!')
#     is_ready_meal = data.get('ready_meal')
#     if is_ready_meal:
#         ingredient = set_ready_meal_tag(ingredient)
#
#     save_m2m_fields(ingredient, data_dict)
#     return ingredient
#
#
# def ingredient_validate_input_data(data: dict) -> None:
#     """ validate incomming data """
#     validate_required_fields(Ingredient, data)
#
#
# def validate_required_fields(model: Union[Recipe, Ingredient], data: dict) -> None:
#     """ check if all required fields are provided """
#     if model == Ingredient:
#         required_fields = ['name']
#         for field in required_fields:
#             if field not in data:
#                 raise ValidationError(f'{field} is required')
#         return
#
#
# def set_ready_meal_tag(instance: Ingredient) -> Ingredient:
#     """ when new ingredient is flagged as ready meal set
#      'Ready Meal' tag to ingredient """
#     tag = Tag.objects.get_or_create(user=instance.user, name='Ready Meal')
#     return save_ingredient_m2m_fields(instance, {'tags': tag})
#
#
# def ingredient_update(ingredient: Ingredient, data: dict, method: str) -> Ingredient:
#     """ update ingredient """
#     return object_update_with_m2m(ingredient, data, method)
#
#
# def object_update_with_m2m(obj: Union[Recipe, Ingredient], data: dict, method: str) -> Union[Recipe, Ingredient]:
#     """ update object with m2m fields """
#     data_dict = pop_m2m_fields(model=obj.__class__, user=obj.user, data=data)
#     if method == 'PUT':
#         clear_m2m_relation(obj)
#     if data.get('name') and obj.name != data['name']:
#         obj.slug = set_slug(obj)
#     for field, value in data.items():
#         setattr(obj, field, value)
#     data_dict.pop('data')
#     save_m2m_fields(obj, data_dict)
#     obj.save()
#     return obj
#     return obj
#     return obj
#     return obj
