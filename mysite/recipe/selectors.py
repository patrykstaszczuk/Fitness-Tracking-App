from django.contrib.auth import get_user_model
from django.http.request import QueryDict
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from recipe.models import Recipe, Ingredient, Unit, Ingredient_Unit, Tag
from users.models import Group
from users import selectors as users_selectors
from typing import Iterable
import requests
import os


def get_recipes(user: get_user_model, url_user: int = None,
                filters: QueryDict = None) -> Iterable[Recipe]:
    """ return all available recipes for user """

    if url_user:
        return Recipe.objects.filter(user=url_user)
    if filters:
        return prepare_queryset(user, filters)
    user_groups = user.membership.all()
    users = get_user_id_from_groups(user_groups)
    return Recipe.objects.filter(user__in=users)


def get_groups_by_ids(group_ids: list[int]) -> Iterable[Group]:
    """ return group based on group id """
    return Group.objects.filter(id__in=group_ids)


def prepare_queryset(user: get_user_model, filters: QueryDict) -> QuerySet:
    """ prepare queryset based on filters """

    queryset = Recipe.objects.filter(user=user)
    allowed_filters = ['tags', 'groups']
    for field in allowed_filters:
        if field in filters:
            list_of_values = filters[field].split(',')
            if field == 'groups':
                queryset = filter_queryset_by_groups(user, list_of_values)
            if field == 'tags':
                queryset = filter_queryset_by_tags(user, list_of_values)
    return queryset


def get_user_id_from_groups(user_groups: Iterable[Group]) -> list[int]:
    """ return user id from groups """
    ids = []
    for group in user_groups:
        ids.append(group.founder.id)
    return ids


def filter_queryset_by_groups(user: get_user_model, list_of_values: list) -> QuerySet:
    """ filter queryset by groups """
    list_of_values = list(map(int, list_of_values))
    group_instances = get_groups_by_ids(list_of_values)

    if len(list_of_values) != group_instances.count():
        raise ValidationError('Invalid group id/ids')

    users_selectors.is_user_in_group(user, group_instances)
    users = get_user_id_from_groups(group_instances)
    return Recipe.objects.filter(user__in=users)


def filter_queryset_by_tags(user: get_user_model, list_of_values: list[str]):
    """ filter queryset by tags """

    map_tags_slug_to_instances(user, list_of_values)
    query = 'tags__slug__in'
    queryset = Recipe.objects.filter(
        user=user).filter(**{query: list_of_values})
    return queryset


def send_ingredients_to_nozbe(slug_list: list) -> bool:
    """ send chosen ingredients to nozbe """

    if is_slug_list_too_long(slug_list):
        return False
    ingredients = ingredient_map_slug_to_object(slug_list)
    secret, client_id, project_id = get_nozbe_request_information()
    for ingredient in ingredients:
        res = send_request_to_nozbe(ingredient, secret, client_id, project_id)
        if res.status_code != 200:
            return False
    return True


def is_slug_list_too_long(slug_list: list) -> bool:
    """ check if list too long """
    return len(slug_list) > 25


def send_request_to_nozbe(ingredient: Ingredient, secret: str, client_id: int,
                          project_id: int) -> requests:
    """ send request to nozbe API """
    url = 'https://api.nozbe.com:3000/task'
    res = requests.post(url, headers={'Authorization': secret},
                        data={'name': ingredient.name, 'project_id':
                              project_id, 'client_id': client_id})
    return res


def ingredient_map_slug_to_object(slug_list: list) -> list[Ingredient]:
    """ map ingredient slug to ingredient instance """
    list_of_instances = []
    for slug in slug_list:
        try:
            ingredient = Ingredient.objects.get(slug=slug)
            list_of_instances.append(ingredient)
        except Ingredient.DoesNotExist:
            raise ValidationError(f'{slug} cannot be mapped to ingredient')
    return list_of_instances


def get_nozbe_request_information() -> tuple([str, str, str]):
    """ return authorization code """
    try:
        return os.environ['NOZBE_SECRET'], os.environ['NOZBE_CLIENT_ID'], \
            os.environ['NOZBE_PROJECT_ID']
    except KeyError:
        raise ValidationError("Cannot retrieve nozbe informations,\
            contanct admin")


def check_if_name_exists(user: get_user_model, name: str) -> int:
    """ return number of recipes with same name and user """
    return Recipe.objects.filter(user=user, name=name).count()


def unit_map_id_to_instance(unit_id: int) -> Unit:
    """ map id to real instance or raise an error """
    try:
        unit = Unit.objects.get(id=unit_id)
    except Unit.DoesNotExist:
        raise ValidationError(f'unit with id ={unit_id} does not exists')
    return unit


def unit_is_mapped_to_ingredient(unit: Unit, ingredient: Ingredient) -> bool:
    """ check if ingredient has been mapped to Unit """
    try:
        Ingredient_Unit.objects.get(ingredient=ingredient, unit=unit)
        return True
    except Ingredient_Unit.DoesNotExist:
        raise ValidationError(f'{ingredient} is has no defined {unit} as unit')
    return False


def map_tags_slug_to_instances(user: get_user_model, tags_slug: list[str]) -> Iterable[Tag]:
    """ map tag's slug string to instances """
    tag_instances = []
    available_tags = Tag.objects.filter(user=user)
    for tag in tags_slug:
        if tag in list(available_tags.values_list('slug', flat=True)):
            tag_instances.append(available_tags.get(slug=tag))
        else:
            raise ValidationError({'tags': f'{tag} does not exsists!'})
    return tag_instances


def map_data_to_instances(user: get_user_model, ingredients: dict) -> dict:
    """ map ingredient slug in data to instances """
    for item in ingredients:
        ingredient_slug = item.get('ingredient')
        unit_id = item.get('unit')

        ingredient = ingredient_map_slug_to_object(
            [ingredient_slug, ])[0]
        item.update({'ingredient': ingredient})
        # try:
        #     instance = Ingredient.objects.get(slug=ingredient_slug)
        #     item.update({'ingredient': instance})
        # except Ingredient.DoesNotExist:
        #     raise ValidationError(
        #         f'{ingredient_slug} such slug does not exists!')

        unit = unit_map_id_to_instance(unit_id)
        if unit_is_mapped_to_ingredient(unit=unit, ingredient=ingredient):
            item.update({'unit': unit})
        # try:
        #     unit = Unit.objects.get(id=unit_id)
        #     item.update({'unit': unit})
        # except Unit.DoesNotExist:
        #     raise ValidationError(f'{unit_id} does not exists!')
    return ingredients


def tags_get(user: get_user_model) -> Iterable[Tag]:
    """ return tag created by user """
    return Tag.objects.filter(user=user)
