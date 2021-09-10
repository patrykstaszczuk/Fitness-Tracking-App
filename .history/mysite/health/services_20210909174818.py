from .models import Meal


def recalculate_total_calories_intake(instanceuser, date) -> int:
    """ recalculate calories based on meals """
    all_meals = Meal.objects.filter(user=user, date=date)
    calories = 0
    for meal in all_meals:
        calories += meal.calories
    return calories