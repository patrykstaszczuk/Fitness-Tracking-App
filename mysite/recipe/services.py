from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.text import slugify
from unidecode import unidecode
from django.core.exceptions import ValidationError
from typing import Iterable
from recipe.models import Recipe, Tag, Ingredient, Recipe_Ingredient, Unit
from recipe import selectors
import os
import shutil


def create_recipe(user: get_user_model, data: dict) -> Recipe:
    """ create recipe based on user and data """

    tags, ingredients, data = pop_m2m_fields(user=user, data=data)
    recipe = Recipe(user=user, **data)
    recipe.slug = set_slug(recipe)
    recipe.save()
    recipe = save_m2m_fields(recipe, tags, ingredients)
    #obj.save()
    return recipe


def set_slug(recipe: Recipe) -> str:
    """ set recipe slug """

    modified_name = ''
    number_of_repeared_names = selectors.check_if_name_exists(
        user=recipe.user, name=recipe.name)
    if number_of_repeared_names > 0:
        modified_name = recipe.name + str(number_of_repeared_names + 1)
    else:
        modified_name = recipe.name
    slug = slugify(unidecode(modified_name))
    return slug


def update_recipe(recipe: Recipe, data: dict, method: str) -> Recipe:
    """ update recipe based on user and data.
     PUT request clears relational field before saving """

    tags, ingredients, data = pop_m2m_fields(user=recipe.user, data=data)
    if method == 'PUT':
        clear_m2m_relation(recipe)
    if data.get('name') and recipe.name != data['name']:
        recipe.slug = set_slug(recipe)
    for field, value in data.items():
        setattr(recipe, field, value)
    recipe = save_m2m_fields(recipe, tags, ingredients)
    recipe.save()
    return recipe


def clear_m2m_relation(instance):
    """ clear m2m relation during PUT request """
    instance.tags.clear()
    instance.ingredients.clear()


def pop_m2m_fields(user: get_user_model, data: dict) -> tuple:
    """ pop relational fields from data and return it """

    tags, ingredients = [], []
    if 'tags' in data:
        tags = data.pop('tags')
        tags = selectors.map_tags_slug_to_instances(user=user, tags_slug=tags)
    if 'ingredients' in data:
        ingredients = data.pop('ingredients')
        ingredients = selectors.map_data_to_instances(
            user=user, ingredients=ingredients)
    return tags, ingredients, data


def save_m2m_fields(obj: Recipe, tags: dict, ingredients: dict) -> Recipe:
    """ save m2m fields. m2m relations are not cleared when using PATCH """
    if tags:
        obj.tags.add(*(tags))
    if ingredients:
        for item in ingredients:
            ingredient = item.pop('ingredient')
            item.update({'recipe': obj})
            obj.ingredients.add(ingredient, through_defaults={**item})
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
            grams = ingredient.convert_unit_to_grams(unit, amount)
            setattr(recipe, field, round((current_recipe_field_value
                                          + (grams/100)*ingredient_field_value), 2))
    kwargs = {'force_insert': False}
    recipe.save(**kwargs, update_fields=['proteins', 'carbohydrates',
                                         'fats', 'calories'])
