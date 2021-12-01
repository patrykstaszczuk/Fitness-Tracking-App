from .models import HealthDiary
from meals_tracker.selectors import meal_list
from health import selectors
from dataclasses import dataclass
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import datetime
import time


@dataclass
class AddStatisticsDto:
    weight: int = None
    sleep_length: str = None
    rest_heart_rate: int = None
    daily_thoughts: str = None

    def __post_init__(self):
        if self.weight and not 20 < self.weight < 300:
            raise ValidationError('Weight must have value between 20 and 300')

        if self.sleep_length:
            format = '%H:%M:%S'
            try:
                time.strptime(self.sleep_length, format)
            except ValueError:
                raise ValidationError(
                    f'Sleep length is in incorrect format: {self.sleep_length}. Proper format: {format}')

        if self.rest_heart_rate and not 0 < self.rest_heart_rate < 230:
            raise ValidationError(
                'Rest heart rate must have value between 0 and 230')


class AddStatistics:
    def add(self, diary: HealthDiary, dto: AddStatisticsDto):
        for attr in vars(dto):
            new_value = getattr(dto, attr)
            if new_value:
                setattr(diary, attr, new_value)
        diary.save()


class RecalculateDiaryCaloriesIntake:
    """ Service called from meals_tracker signals only """

    def recalculate(self, user: get_user_model, date: datetime.date) -> None:
        diary = selectors.health_diary_get(user=user, date=date)
        diary.calories = self._get_calories_from_meals(user, date)
        diary.save()

    def _get_calories_from_meals(user: get_user_model, date: datetime) -> list[int]:
        return sum(list(meal_list(user, date).values_list('calories', flat=True))) or 0


#
# @dataclass
# class HealthService:
#     user: get_user_model
#     instance: HealthDiary
#     data: dict
#
#     def update(self):
#         """ update health diary """
#         for field, value in self.data.items():
#             setattr(self.instance, field, value)
#         self.instance.save()
#         return self.instance
#
#
# def recalculate_total_calories_intake(instance: HealthDiary) -> int:
#     """ recalculate calories based on meals """
#     all_meals = meal_list(user=instance.user, date=instance.date)
#     instance.calories = 0
#     for meal in all_meals:
#        instance.calories += meal.calories
#     return instance.calories
#
#
# def update_health_diary(instance: HealthDiary, data: dict) -> HealthDiary:
#     """ update health diary with given data """
#     for field, value in data.items():
#         setattr(instance, field, value)
#     instance.save()
#     return instance
