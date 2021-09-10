from .models import HealthDiary, Meal
from meals_tracker.selectors import get_meals
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

def update_activities(date: datetime) -> None:
    """ get list of activities from strava for given day
    and add every new activities for db"""

    hour 