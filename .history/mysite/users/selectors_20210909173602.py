from django.contrib.auth import get_user_model
import datetime

def get_activities(user: get_user_model, date: datetime) ->