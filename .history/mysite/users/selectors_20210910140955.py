from typing import Iterable
from django.contrib.auth import get_user_model
import datetime
from users.models import StravaActivity

def get_activities(user: get_user_model, date: datetime) -> Iterable[StravaActivity]:
    """ return strava activities for given date """
    return StravaActivity.objects.filter(user=user, date=date)


def get_strava_last_request_epoc_time(user: get_user_model) -> int:
    """ return last request time in epoc format """
    return user.strava.last_request_epoct_time

def get_activities_from_strava(user: get_user_model, date: datetime) -> dict:
    process_and_save_strava_activities
