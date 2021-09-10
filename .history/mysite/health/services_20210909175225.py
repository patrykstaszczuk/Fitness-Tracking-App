from .models import HealthDiary, Meal
from 

def recalculate_total_calories_intake(instance: HealthDiary) -> int:
    """ recalculate calories based on meals """
    all_meals = Meal.objects.filter(user=user, date=date)
    calories = 0
    for meal in all_meals:
        calories += meal.calories
    return calories