from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from unittest.mock import patch
from health.services import (
    AddStatisticsDto,
    AddStatistics,
    RecalculateDiaryCaloriesIntake,
)
from health.models import HealthDiary

import datetime


class HealthServicesTests(TestCase):

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test100@gmail.com',
            name='testname100',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,)
        self.today = datetime.date.today()

    def _create_diary(self, date: datetime = datetime.date.today()) -> HealthDiary:
        return HealthDiary.objects.create(
            user=self.user,
            date=date,
            slug=slugify(date)
        )

    def test_AddStatistics_to_daily_diary_success(self) -> None:
        diary = self._create_diary()
        dto = AddStatisticsDto(
            weight=75,
            sleep_length='07:00:00',
            rest_heart_rate=45,
            daily_thoughts='some text'
        )
        service = AddStatistics()
        service.add(diary, dto)
        self.assertEqual(diary.weight, dto.weight)

    @patch('health.services.RecalculateDiaryCaloriesIntake._get_calories_from_meals')
    def test_RecalculateDiaryCaloriesIntake_service(self, mock) -> None:
        mock.return_value = 2000
        diary = self._create_diary()
        service = RecalculateDiaryCaloriesIntake()
        service.recalculate(self.user, self.today)
        diary.calories = 2000

    def test_AddStatistics_with_invalid_weigth(self) -> None:
        with self.assertRaises(ValidationError):
            AddStatisticsDto(weight=19)
            AddStatisticsDto(weight=301)

    def test_AddStatistics_with_invalid_sleep_length(self) -> None:
        with self.assertRaises(ValidationError):
            AddStatisticsDto(sleep_length='invalid format')
            AddStatisticsDto(sleep_length=1234)

    def test_AddStatistics_with_invalid_rest_heart_rate(self) -> None:
        with self.assertRaises(ValidationError):
            AddStatisticsDto(rest_heart_rate=-1)
            AddStatisticsDto(rest_heart_rate=231)
