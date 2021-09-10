from .models import HealthDiary, Meal
from meals_tracker.selectors import get_meals

def recalculate_total_calories_intake(instance: HealthDiary) -> int:
    """ recalculate calories based on meals """
    all_meals = get_meals(user=instance.user, date=instance.date)
    calories = 0
    for meal in all_meals:
        calories += meal.calories
    return calories

def update_health_diary(instance: HealthDiary, data: dict) -> HealthDiary:
    """ update health diary with given data """

    for 