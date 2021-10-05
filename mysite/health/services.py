from .models import HealthDiary, Meal
from meals_tracker.selectors import meal_list
from dataclasses import dataclass
from django.contrib.auth import get_user_model


@dataclass
class HealthService:
    user: get_user_model
    instance: HealthDiary
    data: dict

    def update(self):
        """ update health diary """
        for field, value in self.data.items():
            setattr(self.instance, field, value)
        self.instance.save()
        return self.instance


def recalculate_total_calories_intake(instance: HealthDiary) -> int:
    """ recalculate calories based on meals """
    all_meals = meal_list(user=instance.user, date=instance.date)
    instance.calories = 0
    for meal in all_meals:
       instance.calories += meal.calories
    return instance.calories


# def update_health_diary(instance: HealthDiary, data: dict) -> HealthDiary:
#     """ update health diary with given data """
#     for field, value in data.items():
#         setattr(instance, field, value)
#     instance.save()
#     return instance
