from typing import Iterable
from django.contrib.auth import get_user_model
import datetime
from users.models import StravaActivity

def get_activities(user: get_user_model, date: datetime) -> Iterable[StravaActivity]