from typing import Iterable
from django.contrib.auth import get_user_model, authenticate
import datetime
import time
import os
from itertools import chain
import requests
from mysite import settings
from users.models import StravaActivity, StravaApi, Group
from django.core.exceptions import ObjectDoesNotExist, ValidationError


def user_authenticate(credentials: dict) -> get_user_model:
    """ authenticate user with privided credentials """
    email = credentials.pop('email')
    password = credentials.pop('password')
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


def get_activity_properties(activity: dict) -> dict:
    """ return only that properties which are needed """
    defaults = {}
    attributes = ['name', 'calories', 'date']

    for attr in attributes:
        try:
            if attr == 'date':
                date_without_tz = activity['start_date_local'][:-1]
                defaults['date'] = date_without_tz
            else:
              defaults[attr] = activity[attr]
        except KeyError:
            defaults[attr] = None
    return defaults


def get_activities(user: get_user_model, date: datetime) -> Iterable[StravaActivity]:
    """ return strava activities for given date """
    return StravaActivity.objects.filter(user=user, date__date=datetime.date(date.year, date.month, date.day))


def get_strava_last_request_epoc_time(user: get_user_model) -> int:
    """ return last request time in epoc format """
    return user.strava.last_request_epoc_time


def get_activities_from_strava(user: get_user_model, date: datetime = datetime.date.today()) -> dict:

    one_day_in_seconds = 86400
    after_epoch_timestamp = int(time.mktime(
        time.strptime(date.strftime('%Y-%m-%d'), '%Y-%m-%d')))
    before_epoch_timestamp = after_epoch_timestamp + one_day_in_seconds
    params = [
        f'after={after_epoch_timestamp}',
        f'before={before_epoch_timestamp}',
    ]

    strava_obj = user.strava
    if can_request_be_send(strava_obj):
        url = prepare_strava_request_url(id=None, params=params)
        access_token = user.strava.access_token
        header = prepare_authorization_header(strava_obj)
        return process_request(strava_obj, url, header, 'GET')
    return None


def can_request_be_send(strava_obj: StravaApi) -> bool:
    """ check whether request can be send with available inforamtions """
    return is_token_valid(strava_obj) or has_needed_information_for_request(strava_obj) and get_new_strava_access_token(strava_obj)


def is_token_valid(strava_obj: StravaApi) -> bool:
    """ check if token is still valid based on expirations time """
    return strava_obj.expires_at > time.time()


def has_needed_information_for_request(strava_obj: StravaApi) -> bool:
    """ check if StravaApi instance has inforamtions needed for request """
    return all([strava_obj.access_token, strava_obj.refresh_token,       strava_obj.expires_at])


def get_new_strava_access_token(strava_obj: StravaApi) -> bool:
    """ request and save new access token based on refresh token parameter """
    try:
        client_id, client_secret = get_environ_variables()
    except KeyError:
        return False

    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': strava_obj.refresh_token,
        'grant_type': 'refresh_token'
    }
    res = process_request(
        strava_obj, settings.STRAVA_AUTH_URL, payload, 'POST')
    if res:
        try:
            strava_obj.access_token = res['access_token']
            strava_obj.refresh_token = res['refresh_token']
            strava_obj.expires_at = res['expires_at']
            strava_obj.save()
            return True
        except KeyError:
            pass
    return False


def get_environ_variables() -> tuple:
    """ return enviromental variables needed for strava authentication """
    return os.environ['STRAVA_CLIENT_ID'], os.environ['STRAVA_CLIENT_SECRET']


def process_request(strava_obj: StravaApi, url: str, payload: dict, type: str) -> dict:
    """ process strava request/response """

    strava_obj.last_request_epoc_time = time.time()
    strava_obj.save()

    if type == 'GET':
        response = send_get_request_to_strava(url, payload)
    else:
        response = send_post_request_to_strava(url, payload=payload)
    if response:
        if response.status_code == 200:
            return response.json()
        else:
            print(response.json())
    return None


def send_get_request_to_strava(url: str, payload: dict) -> requests:
    """ send request to strava based on parameters """
    print("Request has been sent")
    return requests.get(url, headers=payload)


def send_post_request_to_strava(url: str, payload: dict) -> requests:
    """ send request to strava based on parameters """
    print("Request has been sent")
    return requests.post(url, payload)


def prepare_strava_request_url(id: int, params: list = None) -> str:
    """ prepare strava url for request """
    if id:
        url = f'https://www.strava.com/api/v3/activities/{id}'
    else:
        url = 'https://www.strava.com/api/v3/athlete/activities?'
        for param in params:
            url += param + '&'
    return url


def prepare_authorization_header(strava_obj: StravaApi) -> str:
    """ create authorization header including access token """
    return {'Authorization': f'Bearer {strava_obj.access_token}'}


def is_auth_to_strava(user: get_user_model) -> bool:
    """ check if there is associated and valid StravaApi instance. """
    try:
        obj = StravaApi.objects.get(user=user)
        if has_needed_information_for_request(obj):
            return True
    except StravaApi.DoesNotExist:
        StravaApi.objects.create(user=user)
    return False
