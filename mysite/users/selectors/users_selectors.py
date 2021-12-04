from itertools import chain
from typing import Iterable

from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from users.models import Group


def user_authenticate(email: str, password: str) -> get_user_model:
    user = authenticate(username=email, password=password)
    if not user:
        raise ValidationError(
            'Unable to authenticate with provided credentials')
    return user


def user_get_by_id(id: int) -> get_user_model:
    """ return use for given id"""
    try:
        return get_user_model().objects.get(id=id)
    except get_user_model().DoesNotExist:
        raise ObjectDoesNotExist(f'User with id = {id} does not exists')


def user_get_groups(user: get_user_model) -> Iterable[Group]:
    """ retreive all user group, also pending """
    pending_groups = user.pending_membership.all()
    joins_groups = group_get_membership(user)
    return list(chain(pending_groups, joins_groups))


def user_get_group_pending_membership(user: get_user_model) -> Iterable[int]:
    """ return pending membership for user """
    return user.pending_membership.all()


def group_get_by_user_id(user_id: int) -> Group:
    """ return group created by user with given id  """
    try:
        return Group.objects.get(founder__id=user_id)
    except Group.DoesNotExist:
        raise ObjectDoesNotExist()


def group_get_membership(user: get_user_model) -> Iterable[Group]:
    """ return user group memberships """
    return user.membership.all().prefetch_related('founder', 'members')


def group_retrieve_founders(groups: list[Group]) -> int:
    """ retrieve gorups founders """
    return [user for user in groups.values_list('founder', flat=True)]


def get_bmi(user: get_user_model) -> int:
    """ calculate and return BMI for user """
    return round(user.weight/(user.height/100)**2, 1)
