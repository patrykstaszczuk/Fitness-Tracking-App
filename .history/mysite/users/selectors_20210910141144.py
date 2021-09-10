from typing import Iterable
from django.contrib.auth import get_user_model
import datetime
import time
from users.models import StravaActivity

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
    url = prepare_strava_request_url(id=None, params=params)
    header = create_authorization_header()

    if self._can_request_be_send():
        return self._process_request(url, header, 'GET')
    return None

def prepare_strava_request_url(id: int, params: list) -> str:
    
