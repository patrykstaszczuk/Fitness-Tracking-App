from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.text import slugify
from django.db.utils import IntegrityError
from unidecode import unidecode
from django.core.exceptions import ValidationError
from typing import Iterable, Union
from recipe.models import Recipe, Tag, Ingredient, Recipe_Ingredient, Unit
from recipe import selectors
import os
import shutil
import uuid


def create_recipe(user: get_user_model, data: dict) -> Recipe:
    """ create recipe based on user and data """

    data_dict = pop_m2m_fields(
        model=Recipe, user=user, data=data)
    recipe = Recipe(user=user, **data)
    recipe.slug = set_slug(recipe)
    recipe.save()
    data_dict.pop('data')
    save_m2m_fields(recipe, data_dict)
    return recipe


def set_slug(instance: Union[Tag, Recipe]) -> str:
    """ set recipe slug """

    modified_name = ''

    if isinstance(instance, Ingredient):
        modified_name = slugify(unidecode(instance.name)) + \
                                '-user-' + str(instance.user.id)
    else:
        modified_name = instance.name

    number_of_repeared_names = selectors.check_if_name_exists(instance)
    if number_of_repeared_names > 0:
        modified_name += str(number_of_repeared_names + 1)

    slug = slugify(unidecode(modified_name))
    return slug


def update_recipe(recipe: Recipe, data: dict, method: str) -> Recipe:
    """ update recipe based on user and data.
     PUT request clears relational field before saving """
    return object_update_with_m2m(recipe, data, method)


def recipe_upload_file(recipe: Recipe, data: dict) -> None:
    """ upload file for recipe """
    for item in data:
        setattr(recipe, item, data[item])
    recipe.save()


def clear_m2m_relation(instance):
    """ clear m2m relation during PUT request """
    if isinstance(instance, Recipe):
        instance.tags.clear()
        instance.ingredients.clear()
        return None
    if isinstance(instance, Ingredient):
        instance.tags.clear()
        instance.units.clear()
        return None


def pop_m2m_fields(model: Union[Recipe, Ingredient], user: get_user_model, data: dict) -> tuple:
    """ pop relational fields from data and return it """
    if model == Ingredient:
        return_dict = {'tags': [], 'units': []}
        if 'tags' in data:
            return_dict['tags'] = selectors.map_tags_slug_to_instances(
                user=user, tags_slug=data.pop('tags'))
        if 'units' in data:
            return_dict['units'] = data.pop('units')
            for unit in return_dict['units']:
                unit['unit'] = selectors.unit_map_id_to_instance(unit['unit'])
        return_dict.update({'data': data})
        return return_dict
    elif model == Recipe:
        return_dict = {'tags': [], 'ingredients': []}
        if 'tags' in data:
            return_dict['tags'] = selectors.map_tags_slug_to_instances(
                user=user, tags_slug=data.pop('tags'))
        if 'ingredients' in data:
            return_dict['ingredients'] = selectors.map_data_to_instances(
                user=user, ingredients=data.pop('ingredients'))
        return_dict.update({'data': data})
        return return_dict


def save_m2m_fields(obj: Union[Recipe, Ingredient], fields: dict) -> Recipe:
    """ save m2m fields. m2m relations are not cleared when using PATCH """
    if isinstance(obj, Recipe):
        return save_recipe_m2m_fields(obj, fields)
    if isinstance(obj, Ingredient):
        return save_ingredient_m2m_fields(obj, fields)


def save_recipe_m2m_fields(obj: Recipe, fields: list[Union[Tag, Ingredient]]) -> Recipe:
    """ save m2m field for recipe """
    tags = fields.get('tags')
    ingredients = fields.get('ingredients')

    if tags:
        obj.tags.add(*(tags))
    if ingredients:
        for item in ingredients:
            ingredient = item.pop('ingredient')
            item.update({'recipe': obj})
            obj.ingredients.add(ingredient, through_defaults={**item})
    return obj


def save_ingredient_m2m_fields(obj: Ingredient, fields: dict[list[Union[Tag, Unit]]]) -> Ingredient:
    """ save m2m fiel for ingredinet """
    tags = fields.get('tags')
    units = fields.get('units')
    if tags:
        obj.tags.add(*(tags))
    if units:
        for item in units:
            unit = item.pop('unit')
            item.update({'ingredient': obj})
            obj.units.add(unit, through_defaults={**item})
    return obj


def delete_recipe(instance: Recipe) -> None:
    """ remove recipe from db """
    path = str(settings.MEDIA_ROOT) + \
        "/recipes/" + instance.user.name + "/" + instance.slug
    if os.path.exists(path):
        shutil.rmtree(path)
    instance.delete()


def recalculate_nutritions_values(recipe: Recipe) -> None:
    """ recalculating recipe nutritions values based on ingredients """
    nutritional_fields = ['proteins', 'carbohydrates', 'fats', 'calories']
    for field in nutritional_fields:
        setattr(recipe, field, 0)

    for ingredient in recipe.ingredients.all():
        obj = Recipe_Ingredient.objects.get(recipe=recipe,
                                            ingredient=ingredient)
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


def tag_create(user: get_user_model, data: dict) -> Tag:
    """ create Tag """
    data.update({'user': user})
    try:
        tag = Tag.objects.create(**data)
    except IntegrityError:
        raise ValidationError('Tag with provided name already exists!')
    tag.slug = set_slug(tag)
    tag.save()
    return tag


def tag_update(tag: Tag, data: dict) -> Tag:
    """ update Tag """

    for attr in data:
        setattr(tag, attr, data[attr])
    if 'name' in data:
        tag.slug = set_slug(tag)
    tag.save()
    return tag


def ingredient_create(user: get_user_model, data: dict) -> Ingredient:
    """ create Ingredient """
    ingredient_validate_input_data(data)
    data_dict = pop_m2m_fields(model=Ingredient, user=user, data=data)
    ingredient = Ingredient()
    for attr, value in data_dict['data'].items():
        setattr(ingredient, attr, value)
    data_dict.pop('data')
    ingredient.user = user
    ingredient.slug = set_slug(ingredient)
    try:
        ingredient.save()
    except IntegrityError:
        raise ValidationError(
            f'Ingredient with name "{ingredient.name}" for user id {user.id} already exsists!')
    is_ready_meal = data.get('ready_meal')
    if is_ready_meal:
        ingredient = set_ready_meal_tag(ingredient)

    save_m2m_fields(ingredient, data_dict)
    return ingredient


def ingredient_validate_input_data(data: dict) -> None:
    """ validate incomming data """
    validate_required_fields(Ingredient, data)


def validate_required_fields(model: Union[Recipe, Ingredient], data: dict) -> None:
    """ check if all required fields are provided """
    if model == Ingredient:
        required_fields = ['name']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f'{field} is required')
        return


def set_ready_meal_tag(instance: Ingredient) -> Ingredient:
    """ when new ingredient is flagged as ready meal set
     'Ready Meal' tag to ingredient """
    tag = Tag.objects.get_or_create(user=instance.user, name='Ready Meal')
    return save_ingredient_m2m_fields(instance, {'tags': tag})


def ingredient_update(ingredient: Ingredient, data: dict, method: str) -> Ingredient:
    """ update ingredient """
    return object_update_with_m2m(ingredient, data, method)


def object_update_with_m2m(obj: Union[Recipe, Ingredient], data: dict, method: str) -> Union[Recipe, Ingredient]:
    """ update object with m2m fields """
    data_dict = pop_m2m_fields(model=obj.__class__, user=obj.user, data=data)
    if method == 'PUT':
        clear_m2m_relation(obj)
    if data.get('name') and obj.name != data['name']:
        obj.slug = set_slug(obj)
    for field, value in data.items():
        setattr(obj, field, value)
    data_dict.pop('data')
    save_m2m_fields(obj, data_dict)
    obj.save()
    return obj
