from .models import HealthDiary, Meal
from meals_tracker.selectors import get_meals
from users.selectors import get_strava_last_request_epoc_time, get_activities_from_strava,   process_and_save_strava_activities, prepare_strava_request_url, prepare_authorization_header, process_request
import datetime
from django.contrib.auth import get_user_model

def recalculate_total_calories_intake(instance: HealthDiary) -> int:
    """ recalculate calories based on meals """
    all_meals = get_meals(user=instance.user, date=instance.date)
    calories = 0
    for meal in all_meals:
        calories += meal.calories
    return calories

def update_health_diary(instance: HealthDiary, data: dict) -> HealthDiary:
    """ update health diary with given data """
    for field, value in data.items():
        setattr(instance, field, value)
    instance.save()
    return instance

