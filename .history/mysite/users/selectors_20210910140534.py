from typing import Iterable
from django.contrib.auth import get_user_model
import datetime
from users.models import StravaActivity

def get_activities(user: get_user_model, date: datetime) -> Iterable[StravaActivity]:
    """ return strava activities for given date """
    return StravaActivity.objects.filter(user=user, date=date)

def get_activities_from_strava(raw_activities: list) -> Itera