from django.contrib.auth import get_user_model
from users import selectors
from users.models import StravaActivity, StravaApi
from mysite import settings
import time
import datetime


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
        print('To many request try again soon. One request per hour is permitted')


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
