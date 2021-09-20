from .models import HealthDiary, Meal
from meals_tracker.selectors import meal_list


def recalculate_total_calories_intake(instance: HealthDiary) -> int:
    """ recalculate calories based on meals """
    all_meals = meal_list(user=instance.user, date=instance.date)
    instance.calories = 0
    for meal in all_meals:
       instance.calories += meal.calories
    return instance.calories


def update_health_diary(instance: HealthDiary, data: dict) -> HealthDiary:
    """ update health diary with given data """
    for field, value in data.items():
        setattr(instance, field, value)
    instance.save()
    return instance
