from .models import HealthDiary, Meal
from meals_tracker.selectors import get_meals
from users.selectors import get_strava_last_request_epoc_time, get_strava_activities
import datetime

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

def update_activities(user: get_user_model, date: datetime) -> None:
    """ get list of activities from strava for given day
    and add every new activities for db"""

    hour = 3600

    if get_strava_last_request_epoc_time(user=user) > hour:
         raw_strava_activities = strava_api_instance.get_strava_activities(
#                 date=instance.date)
#             if raw_strava_activities and isinstance(raw_strava_activities, list):
#                 strava_api_instance.process_and_save_strava_activities(
#                     raw_strava_activities)
    return None