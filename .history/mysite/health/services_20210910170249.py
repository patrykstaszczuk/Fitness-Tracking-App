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

def update_activities(user: get_user_model, date: datetime) -> None:
    """ get list of activities from strava for given day
    and add every new activities for db"""

    hour = 3600
    raw_strava_activities = []
    if get_strava_last_request_epoc_time(user=user) > hour:
        raw_strava_activities = get_activities_from_strava(user=user, date=date)
        process_and_save_strava_activities(user, raw_strava_activities)

def process_and_save_strava_activities(user: get_user_model, raw_strava_activities: list) -> None:
    """ convert raw activities into StravaActivity objects
    """
    if raw_strava_activities and isinstance(raw_strava_activities, list):
        activity_objects = []
        for activity in raw_strava_activities:
            strava_id = activity.get('id', None)
            if not strava_id:
                continue
            url = prepare_strava_request_url(id=strava_id)
            header = prepare_authorization_header(strava_obj=user.strava)
            strava_activity = process_request(url, header, 'GET')
            if raw_activity_details:
                defaults = get_activity_details(raw_activity_details)
                obj, created = StravaActivity.objects.update_or_create(
                    strava_id=strava_id, user=self.user, **defaults)
                activity_objects.append(obj)
        return activity_objects
    return None