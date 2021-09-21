from users import selectors
import datetime
import time
from mysite import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from users.models import StravaActivity, StravaApi


def create_user(data: dict) -> get_user_model:
    """ create user based on data """
    return get_user_model().objects.create_user(**data)


def update_user(user: get_user_model, data: dict) -> get_user_model:
    """ update user based on provided data """
    for attr, value in data.items():
        setattr(user, attr, value)
    user.save()
    return user


def change_password(user: get_user_model, data: dict) -> None:
    """ update user password """
    if 'password' in data:
        user.set_password(data['password'])
        user.save()
    return user


def send_group_invitation(user: get_user_model, data: dict[int]) -> bool:
    """ set pending membership for users IDs in data """
    for user_id in data['pending_membership']:
        try:
            invited_user = selectors.get_user(user_id['id'])
        except ObjectDoesNotExist:
            raise ValidationError('User with provided id does not exists!')
        if invited_user == user:
            raise ValidationError('You cannot invite yourself')
        invited_user.pending_membership.add(user.own_group.id)


def manage_group_invitation(user: get_user_model, data: dict) -> bool:
    """ manage group invitation based of data """

    if data['action'] == 1:
        accept_group_invitation(user, data['pending_membership'])
    else:
        deny_group_invitation(user, data['pending_membership'])


def accept_group_invitation(user: get_user_model, groups_ids: list[int]) -> bool:
    """ add group_id to user membership and remove from pending membership """

    for group_id in groups_ids:
        user.membership.add(group_id['id'])
        user.pending_membership.remove(group_id['id'])


def deny_group_invitation(user: get_user_model, groups_ids: list[int]) -> bool:
    """ remove group id from user pending membership """
    for group_id in groups_ids:
        user.pending_membership.remove(group_id['id'])


def leave_group(user: get_user_model, group_id: int) -> None:
    """ remove group from user membership """
    group_id = group_id.get('id')
    if not isinstance(group_id, int):
        raise ValidationError('group_id must be a number!')
    if user.own_group.id == group_id:
        raise ValidationError('You cannot leave own group!')

    group = selectors.get_groups_by_ids([group_id, ]).first()
    if not group:
        raise ValidationError('Such group does not exists')
    if selectors.is_user_in_group(user, [group, ]):
        user.membership.remove(group)


def authorize_to_strava(user: get_user_model, strava_code: str) -> bool:
    try:
        client_id, client_secret = selectors.get_environ_variables()
    except KeyError:
        return False
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": strava_code,
        "grant_type": "authorization_code"
    }
    strava_obj = StravaApi.objects.get_or_create(user=user)[0]
    url = settings.STRAVA_AUTH_URL
    res = selectors.process_request(
        strava_obj, url=url, payload=payload, type='POST')
    if res:
        important_auth_data = {'expires_at': None, 'refresh_token': None,
                               'access_token': None}
        if all(attr in res for attr in important_auth_data.keys()):
            for data in important_auth_data.keys():
                setattr(strava_obj, data, res[data])
            strava_obj.save()
            return True
        return False


def update_activities(user: get_user_model, date: datetime) -> None:
    """ get list of activities from strava for given day
    and add every new activities for db"""
    now = time.time()
    hour = 3600
    raw_strava_activities = []
    if now - selectors.get_strava_last_request_epoc_time(user=user) > hour:
        raw_strava_activities = selectors.get_activities_from_strava(
            user=user, date=date)
        process_and_save_strava_activities(user, raw_strava_activities)
    else:
        print('To many request try again soon')


def process_and_save_strava_activities(user: get_user_model, raw_strava_activities: list) -> None:
    """ convert raw activities into StravaActivity objects
    """
    if raw_strava_activities and isinstance(raw_strava_activities, list):
        activity_objects = []
        for activity in raw_strava_activities:
            strava_id = activity.get('id', None)
            if not strava_id:
                continue
            url = selectors.prepare_strava_request_url(id=strava_id)
            header = selectors.prepare_authorization_header(
                strava_obj=user.strava)
            strava_activity = selectors.process_request(
                user.strava, url, header, 'GET')
            if strava_activity:
                defaults = selectors.get_activity_properties(strava_activity)
                obj, created = StravaActivity.objects.update_or_create(
                    strava_id=strava_id, user=user, **defaults)
                activity_objects.append(obj)
        return activity_objects
    return None