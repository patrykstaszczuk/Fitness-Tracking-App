from .models import Meal


def recalculate_total_calories_intake(self, user, date) -> int:
    """ recalculate calories based on meals """
    all_meals = Meal.objects.filter(user=self.user, date=self.date)
    calories = 0
    for meal in all_meals:
        calories += meal.calories
    return calories