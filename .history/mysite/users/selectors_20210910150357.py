from typing import Iterable
from django.contrib.auth import get_user_model
import datetime
import time
from users.models import StravaActivity, StravaApi

def get_activities(user: get_user_model, date: datetime) -> Iterable[StravaActivity]:
    """ return strava activities for given date """
    return StravaActivity.objects.filter(user=user, date=date)


def get_strava_last_request_epoc_time(user: get_user_model) -> int:
    """ return last request time in epoc format """
    return user.strava.last_request_epoct_time

def get_activities_from_strava(user: get_user_model, date: datetime) -> dict:

    one_day_in_seconds = 86400
    after_epoch_timestamp = int(time.mktime(time.strptime(date.strftime('%Y-%m-%d'), '%Y-%m-%d')))
    before_epoch_timestamp = after_epoch_timestamp + one_day_in_seconds
    params = [
        f'after={after_epoch_timestamp}',
        f'before={before_epoch_timestamp}',
    ]

    if can_request_be_send(strava_obj=user.strava):
        url = prepare_strava_request_url(id=None, params=params)
        access_token = user.strava.access_token
        header = prepare_authorization_header()

    # if self._can_request_be_send():
    #     return self._process_request(url, header, 'GET')
    # return None

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
        client_id, client_secret = se.user.get_environ_variables()
    except KeyError:
        return False

    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': self.refresh_token,
        'grant_type': 'refresh_token'
    }
    res = self._process_request(settings.STRAVA_AUTH_URL, payload, 'POST')

    if res:
        try:
            self.access_token = res['access_token']
            self.refresh_token = res['refresh_token']
            self.expires_at = res['expires_at']
            self.save()
            return True
        except KeyError:
            pass
    return False


def prepare_strava_request_url(id: int, params: list) -> str:
    """ prepare strava url for request """
    if id:
        url = f'https://www.strava.com/api/v3/activities/{id}'
    else:
        url = 'https://www.strava.com/api/v3/athlete/activities?'
        for param in params:
            url += param + '&'
    return url

def prepare_authorization_header():
    """ create authorization header including access token """
    return {'Authorization': f'Bearer {self.access_token}'}
