from django.contrib.auth import get_user_model
from django.http.request import QueryDict
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models.query import QuerySet
from recipe.models import Recipe, Ingredient, Unit, Ingredient_Unit, Tag
from users.models import Group
from users import selectors as users_selectors
from typing import Iterable, Union, List
import requests
import os


def recipe_get(user: get_user_model, slug: str) -> Recipe:
    """ return recipe object """
    try:
        return Recipe.objects.get(user=user, slug=slug)
    except ValueError as e:
        raise ValidationError(e)
    except ObjectDoesNotExist:
        raise ObjectDoesNotExist(
            f'Recipe with provided slug {slug} does not exists!')


def recipe_list(user: get_user_model, filters: QueryDict = None) -> list[Recipe]:
    """ retrieve list of recipes """
    user_groups = users_selectors.group_get_membership(user)
    list_of_users_ids = users_selectors.group_retrieve_founders(user_groups)

    default_queryset = Recipe.objects.filter(
        user__id__in=list_of_users_ids).prefetch_related('tags', 'ingredients')
    if filters:
        return filter_queryset(user, filters, default_queryset)
    return default_queryset


def filter_queryset(user: get_user_model, filters: QueryDict, default_queryset: QuerySet) -> list[Recipe]:
    """ apply filters on queryset and return it """
    queryset = default_queryset
    allowed_filters = ['tags', 'groups']
    for field in allowed_filters:
        if field in filters:
            list_of_values = filters[field].split(',')
            if field == 'groups':
                queryset = filter_queryset_by_groups(
                    user, list_of_values, queryset)
            if field == 'tags':
                queryset = filter_queryset_by_tags(
                    user, list_of_values, queryset)
    return queryset


def filter_queryset_by_groups(user: get_user_model, list_of_values: list, queryset: QuerySet) -> QuerySet:
    """ filter queryset by groups """
    list_of_values = list(map(int, list_of_values))
    group_instances = users_selectors.get_groups_by_ids(list_of_values)

    if len(list_of_values) != group_instances.count():
        raise ValidationError('Invalid group id/ids')

    users_selectors.is_user_in_group(user, group_instances)
    users = groups_retrieve_founders(group_instances)
    return queryset.filter(user__in=users)


def filter_queryset_by_tags(user: get_user_model, list_of_values: list[str], queryset: QuerySet):
    """ filter queryset by tags """

    map_tags_slug_to_instances(user, list_of_values)
    query = 'tags__slug__in'
    return queryset.filter(
        user=user).filter(**{query: list_of_values})


def recipe_check_if_user_can_retrieve(requested_user: get_user_model,
                                      recipe_creator_id: int) -> None:
    """ check if requested user can view recipes created by specific user """
    recipe_creator_group = users_selectors.group_get_by_user_id(
        recipe_creator_id)
    try:
        if requested_user not in recipe_creator_group.members.all():
            raise ValidationError('You are not a member of given user group!')
    except AttributeError as e:
        print(f'{e} func: recipe_check_if_user_can_retrieve')
        raise ValidationError('Internal error, contanct administrator')


def recipe_calculate_calories_based_on_portion(portion: int, recipe: Recipe) -> int:
    """ return recipe calories based on portion """
    return portion * (recipe.calories/recipe.portions)


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


def check_if_name_exists(instance: Union[Tag, Recipe]) -> int:
    """ return number of recipes with same name and user """
    return Recipe.objects.filter(user=instance.user, name=instance.name).count()


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

        unit = unit_map_id_to_instance(unit_id)
        if unit_is_mapped_to_ingredient(unit=unit, ingredient=ingredient):
            item.update({'unit': unit})
    return ingredients


def tag_list(user: get_user_model) -> Iterable[Tag]:
    """ return tags created by user """
    return Tag.objects.filter(user=user)


def tag_get(user: get_user_model, slug: str) -> Tag:
    """ return tag object """
    try:
        return Tag.objects.get(user=user, slug=slug)
    except Tag.DoesNotExist:
        raise ObjectDoesNotExist(f"Tag with slug {slug} does not exists!")


def tag_get_multi_by_slugs(user: get_user_model, slugs: list[str]) -> list[Tag]:
    """ return tags by provided slugs or raise error """
    tag_instances = Tag.objects.filter(user=user, slug__in=slugs)
    if len(tag_instances) != len(slugs):
        raise ObjectDoesNotExist(
            'At least one of proviede slug cannot be mapped to tag')
    return tag_instances


def ingredient_list(user: get_user_model) -> Iterable[Ingredient]:
    """ return ingredients created by user """
    return Ingredient.objects.all()


def ingredient_get(slug: str) -> Ingredient:
    """ return ingredient object. Ingrediens are common whats why
     we dont filter queryset by user """
    try:
        return Ingredient.objects.get(slug=slug)
    except Ingredient.DoesNotExist:
        raise ObjectDoesNotExist(
            f"Ingredient with slug {slug} does not exists!")


def ingredient_get_multi_by_slugs(slugs: list[str]) -> list[Ingredient]:
    """ return ingredients by provided slugs or raise error if not exists """
    ingredient_instances = Ingredient.objects.filter(slug__in=slugs)
    if len(ingredient_instances) != len(slugs):
        raise ObjectDoesNotExist(
            'At least one of provided slug cannot be mapped to ingredient')
    return ingredient_instances


def ingredient_get_for_requested_user(user: get_user_model, slug: str) -> Ingredient:
    """ filter all ingredients by requested user """
    try:
        return Ingredient.objects.get(user=user, slug=slug)
    except Ingredient.DoesNotExist:
        raise ObjectDoesNotExist(
            f"Ingredient with slug {slug} does not exists!")


def ingredient_get_available_units(ingredient: Ingredient) -> Iterable[Ingredient_Unit]:
    """ return available units for ingredient """
    return Ingredient_Unit.objects.filter(ingredient=ingredient)


def ingredient_convert_unit_to_grams(ingredient: Ingredient, unit: Unit, amount: int) -> int:
    """ convert amount of given unit to amount of given unit in grams """
    if unit.name == 'gram':
        return amount
    try:
        obj = Ingredient_Unit.objects.get(
            ingredient=ingredient.id, unit=unit)
    except Ingredient_Unit.DoesNotExist:
        raise ValidationError(f"{unit} - {ingredient.name} no such mapping")
    return obj.grams_in_one_unit * amount


def ingredient_calculate_calories(ingredient: Ingredient, unit: Unit, amount: int) -> int:
    """ return calcualted calories based on unit and amount """
    return (ingredient_convert_unit_to_grams(ingredient, unit, amount)/100) * ingredient.calories


def unit_get(id: int, default: bool) -> Unit:
    """ return unit """
    if default:
        return Unit.objects.get_or_create(name='gram')
    return Unit.objects.get(id=id)


def unit_list() -> Iterable[Unit]:
    """ return all available units """
    return Unit.objects.all()
    return Unit.objects.all()
    return Unit.objects.all()
    return Unit.objects.all()
    return Unit.objects.all()
    return Unit.objects.all()
    return Unit.objects.all()
