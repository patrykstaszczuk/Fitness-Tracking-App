from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from typing import Iterable
from recipe.models import Recipe, Tag, Ingredient, Recipe_Ingredient, Unit

def create_recipe(user: get_user_model, data: dict) -> Recipe:
    """ create recipe based on user and data """

    tags, ingredients, data = pop_m2m_fields(data)
    obj = Recipe.objects.create(user=user, **data)
    obj = save_m2m_fields(obj, tags, ingredients)
    obj.save()
    return obj

def update_recipe(instance: Recipe, data: dict, method: str) -> Recipe:
    """ update recipe based on user and data """

    tags, ingredients, data = pop_m2m_fields(data)

    if method == 'PATCH':
        instance = update_obj_with_patch(instance, data)
    else:
        instance = update_obj_with_put(instance, data)

    instance = save_m2m_fields(instance, tags, ingredients)
    return instance

    for field, value in data.items():
        setattr(instance, field, value)
    instance = save_m2m_fields(instance, tags, ingredients)
    instance.save()
    return instance

def update_obj_with_patch(instance: Recipe, data: dict) -> Recipe:
    """ handle patch update """
    for field, value in data.items():
        setattr(instance, field, value)
    return instance

def update_obj_with_put(instance: Recipe, data: dict) -> Recipe:
    """ handle put update """
    for attr in instance:
        print(attr)

def pop_m2m_fields(data: dict) -> tuple(list, dict):
    """ pop relational fields from data and return it """

    tags, ingredients = [], []
    if 'tags' in data:
        tags = data.pop('tags')
    if 'ingredients' in data:
        ingredients = data.pop('ingredients')
    return tags, ingredients, data

def save_m2m_fields(obj: Recipe, tags: dict, ingredients: dict) -> Recipe:
    """ save m2m fields """
    if tags:
        tags = map_tags_slug_to_instances(user=obj.user, tags_slug=tags)
        obj.tags.add(*(tags))
    if ingredients:
        ingredients = map_data_to_instances(user=obj.user, ingredients=ingredients)
        for ingredient in ingredients:
            Recipe_Ingredient.objects.create(recipe=obj, **ingredient)
    return obj

def map_tags_slug_to_instances(user: get_user_model, tags_slug: list[str]) -> Iterable[Tag]:
    """ map tag's slug string to instances """
    tag_instances = []
    all_user_tags = list(Tag.objects.filter(user=user))

    for tag in all_user_tags:
        if tag.slug in tags_slug:
            tag_instances.append(tag.id)

    if len(tags_slug) != len(tags_slug):
        raise ValidationError({'tags': 'One of the tag slug does not exists!'})
    return tag_instances

def map_data_to_instances(user: get_user_model, ingredients: dict) -> dict:
    """ map ingredient slug in data to instances """
    for item in ingredients:
        ingredient_slug = item.get('ingredient')
        unit_id = item.get('unit')
        try:
            instance = Ingredient.objects.get(slug=ingredient_slug)
            item.update({'ingredient': instance})
        except Ingredient.DoesNotExist:
            raise ValidationError(f'{ingredient_slug} such slug does not exists!')
        try:
            unit = Unit.objects.get(id=unit_id)
            item.update({'unit': unit})
        except Unit.DoesNotExist:
            raise ValidationError(f'{unit_id} does not exists!')
    return ingredients


