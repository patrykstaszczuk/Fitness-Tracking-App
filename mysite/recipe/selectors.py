from django.contrib.auth import get_user_model
from django.http.request import QueryDict
from django.db.models.query import QuerySet
from recipe.models import Recipe
from users.models import Group
from typing import Iterable


def get_recipes(user: get_user_model, url_user: int=None, filters: QueryDict=None) -> Iterable[Recipe]:
    """ return all available recipes for user """

    if url_user:
        return Recipe.objects.filter(user=url_user)
    if filters:
        return prepare_queryset(user, filters)
    user_groups = user.membership.all()
    users = get_user_id_from_groups(user_groups)
    return Recipe.objects.filter(user__in=users)

def prepare_queryset(user: get_user_model, filters: QueryDict) -> QuerySet:
    """ prepare queryset based on filters """
    queryset = Recipe.objects.filter(user=user)
    allowed_filters = ['tags', 'groups']
    for field in allowed_filters:
        if field in filters:
            list_of_values = filters[field].split(',')
            query = field + '__slug__in'
            queryset = queryset.filter(**{query: list_of_values})
    return queryset

def get_user_id_from_groups(user_groups: Iterable[Group]) -> list[int]:
    """ return user id from groups """
    ids = []
    for group in user_groups:
        ids.append(group.founder.id)
    return ids