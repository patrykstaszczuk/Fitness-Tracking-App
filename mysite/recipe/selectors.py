from django.contrib.auth import get_user_model
from django.http.request import QueryDict
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models.query import QuerySet
from recipe.models import Recipe, Ingredient, Unit, Ingredient_Unit, Tag, Recipe_Ingredient
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


def recipe_get_tags(user: get_user_model, recipe: Recipe) -> Iterable[Tag]:
    """ return all tags for given recipe """
    return Tag.objects.filter(user=user, recipe=recipe)


def recipe_get_ingredients(recipe: Recipe) -> Iterable[Ingredient]:
    """ return all ingredients with unit and amount for given recipe """
    return Recipe_Ingredient.objects.filter(recipe=recipe).prefetch_related('ingredient', 'unit')


def recipe_get_ingredient_details(recipe: Recipe, ingredient_id: str) -> Recipe_Ingredient:
    """ return specific recipe ingredient intermediate table object """
    try:
        return recipe.ingredients_quantity.get(ingredient__id=ingredient_id)
    except ValueError as e:
        raise ValidationError(e)


def recipe_list(user: get_user_model, filters: QueryDict = None) -> list[Recipe]:
    """ retrieve list of recipes """
    user_groups = users_selectors.group_get_membership(user)
    list_of_users_ids = users_selectors.group_retrieve_founders(user_groups)
    # default_queryset = Recipe.objects.filter(
    #     user__id__in=list_of_users_ids).prefetch_related('tags', 'ingredients')
    default_queryset = Recipe.objects.filter(
        user__id__in=list_of_users_ids).prefetch_related('user')
    if filters:
        return filter_queryset(user, filters, default_queryset, user_groups)
    return default_queryset


def filter_queryset(user: get_user_model, filters: QueryDict, default_queryset: QuerySet, user_groups: list[Group]) -> list[Recipe]:
    """ apply filters on queryset and return it """
    queryset = default_queryset
    allowed_filters = ['tags', 'groups']
    for field in allowed_filters:
        if field in filters:
            list_of_values = filters[field].split(',')
            if field == 'groups':
                queryset = filter_queryset_by_groups(
                    list_of_values, queryset, user_groups)
            if field == 'tags':
                queryset = filter_queryset_by_tags(
                    user, list_of_values, queryset)
    return queryset


def filter_queryset_by_groups(list_of_values: list, queryset: QuerySet, user_groups: list[Group]) -> QuerySet:
    """ filter queryset by groups """
    list_of_values = list(map(int, list_of_values))
    group_ids = user_groups.values_list('id', flat=True)
    if not all(list_of_values[id] in group_ids for id in range(len(list_of_values))):
        raise ValidationError('Invalid group id/ids')
    return queryset.filter(user__own_group__id__in=list_of_values)


def filter_queryset_by_tags(user: get_user_model, tag_slugs: list[str], queryset: QuerySet):
    """ filter queryset by tags """
    tags_instances = tag_get_multi_by_slugs(user, tag_slugs)
    return queryset.filter(tags__in=list(tags_instances))


def recipe_check_if_user_can_retrieve(requested_user: get_user_model,
                                      recipe_creator_id: int) -> None:
    """ check if requested user can view recipes created by specific user """
    try:
        recipe_creator_id = int(recipe_creator_id)
    except ValueError:
        raise ObjectDoesNotExist()
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


def tag_list(user: get_user_model) -> Iterable[Tag]:
    """ return tags created by user """
    return Tag.objects.filter(user=user)


def tag_ids_list(user: get_user_model) -> list[int]:
    """ return tags ids for given user """
    return tag_list(user).values_list('id', flat=True)


def tag_list_by_user_and_recipe(user: get_user_model, recipe_slug: str) -> list[Tag]:
    """ return tags assigned to given recipe """
    return Tag.objects.filter(user=user, recipe__slug=recipe_slug)


def tag_get(user: get_user_model, slug: str) -> Tag:
    """ return tag object """
    try:
        return Tag.objects.get(user=user, slug=slug)
    except Tag.DoesNotExist:
        raise ObjectDoesNotExist(f"Tag with slug {slug} does not exists!")


def tag_ready_meal_get_or_create(user: get_user_model) -> Tag:
    """ return 'ready meal' tag or create and return """
    return Tag.objects.get_or_create(user=user, slug='ready-meal', defaults={'name': 'Ready Meal'})


def tag_get_multi_by_slugs(user: get_user_model, slugs: list[str]) -> list[Tag]:
    """ return tags by provided slugs or raise error """
    tag_instances = Tag.objects.filter(user=user, slug__in=slugs)
    if len(tag_instances) != len(slugs):
        raise ObjectDoesNotExist(
            'At least one of proviede slug cannot be mapped to tag')
    return tag_instances


def ingredient_list() -> Iterable[Ingredient]:
    """ return all ingredients """
    return Ingredient.objects.all().prefetch_related('tags')


def ingredient_get(slug: str) -> Ingredient:
    """ return ingredient object. Ingrediens are common whats why
     we dont filter queryset by user """
    try:
        return Ingredient.objects.get(slug=slug)
    except Ingredient.DoesNotExist:
        raise ObjectDoesNotExist(
            f"Ingredient with slug {slug} does not exists!")


def ingredient_get_tags(ingredient: Ingredient) -> Iterable[Tag]:
    """ retrieve all tags for given ingredient """
    return ingredient.tags.all()


def ingredient_get_units(ingredient: Ingredient) -> Iterable[Unit]:
    """ retreve all units for given ingredient """
    return ingredient.units.all()


def ingredient_get_only_for_user(user: get_user_model, slug: str) -> Ingredient:
    """ return ingredient only for requested user """
    try:
        return Ingredient.objects.get(user=user, slug=slug)
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
    if ingredient.calories is None:
        return None
    return round((ingredient_convert_unit_to_grams(ingredient, unit, amount)/100) * ingredient.calories, 2)


def ingredient_send_to_nozbe(slug_list: list) -> bool:
    """ send chosen ingredients to nozbe """

    if is_slug_list_too_long(slug_list):
        return False
    ingredients = ingredient_get_multi_by_slugs(slug_list)
    secret, client_id, project_id = get_nozbe_request_information()
    for ingredient in ingredients:
        res = send_request_to_nozbe(ingredient, secret, client_id, project_id)
        if res.status_code != 200:
            return False
    return True


def is_slug_list_too_long(slug_list: list) -> bool:
    """ check if list too long """
    return len(slug_list) > 25


def get_nozbe_request_information() -> tuple([str, str, str]):
    """ return authorization code """
    try:
        return os.environ['NOZBE_SECRET'], os.environ['NOZBE_CLIENT_ID'], \
            os.environ['NOZBE_PROJECT_ID']
    except KeyError:
        raise ValidationError("Cannot retrieve nozbe informations,\
            contanct admin")


def send_request_to_nozbe(ingredient: Ingredient, secret: str, client_id: int,
                          project_id: int) -> requests:
    """ send request to nozbe API """
    url = 'https://api.nozbe.com:3000/task'
    res = requests.post(url, headers={'Authorization': secret},
                        data={'name': ingredient.name, 'project_id':
                              project_id, 'client_id': client_id})
    return res


def unit_get(id: int, default: bool) -> Unit:
    """ return unit """
    if default:
        return Unit.objects.get_or_create(name='gram')
    try:
        return Unit.objects.get(id=id)
    except Unit.DoesNotExist:
        raise ObjectDoesNotExist(f'No unit with id {id}')


def unit_list() -> Iterable[Unit]:
    """ return all available units """
    return Unit.objects.all()


def unit_get_multi_by_ids(ids: list[int]) -> list[Unit]:
    """ return units by provided ids or raise object does not exists """
    all_units = Unit.objects.all()
    mapped_instances = []
    for id in ids:
        try:
            mapped_instances.append(all_units.get(id=id))
        except Unit.DoesNotExist:
            raise ObjectDoesNotExist(f'Unit with id {id} does not exists!')
    return mapped_instances


# def unit_is_mapped_to_ingredient(unit: Unit, ingredient: Ingredient) -> bool:
#     """ check if ingredient has been mapped to Unit """
#     try:
#         Ingredient_Unit.objects.get(ingredient=ingredient, unit=unit)
#         return True
#     except Ingredient_Unit.DoesNotExist:
#         raise ValidationError(f'{ingredient} is has no defined {unit} as unit')
#     return False
