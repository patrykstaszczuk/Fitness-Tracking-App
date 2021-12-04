import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from health import selectors

HEALTH_DIARY_LIST = reverse('health:health-diary-list')


def health_statistic_url(name: str) -> reverse:
    return reverse('health:health-statistic', kwargs={'name': name})


def health_diary_detail_url(slug: str) -> reverse:
    return reverse('health:health-diary-detail', kwargs={'slug': slug})


class HealthApiTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='auth@gmail.com',
            name='auth',
            password='authpass',
            gender='M',
            age=25,
            height=188,
            weight=73,

        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.today = datetime.date.today()

    @staticmethod
    def _create_diary(user: get_user_model, date: datetime = datetime.date.today()) -> None:
        return selectors.health_diary_get(user, date)

    def test_add_statistics_to_todays_diary(self) -> None:
        date = str(self.today)
        payload = {
            'weight': 74.3,
            'sleep_length': '07:24:00',
            'daily_thoughts': 'This will be a greate day!'
        }
        res = self.client.post(health_diary_detail_url(date), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data['weight'], payload['weight'])
        self.assertEqual(res.data['sleep_length'], payload['sleep_length'])

    def test_add_statistics_to_todays_diary_with_invalid_value_failed(self) -> None:
        date = str(self.today)
        payload = {
            'weight': 12321321321321,
            'sleep_length': '07:24:00',
            'daily_thoughts': 'This will be a greate day!'
        }
        res = self.client.post(health_diary_detail_url(date), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adding_statistics_to_diary_in_the_future_failed(self) -> None:
        date = str(self.today + datetime.timedelta(1))
        payload = {
            'weight': 75,
            'sleep_length': '07:24:00',
            'daily_thoughts': 'This will be a greate day!'
        }
        res = self.client.post(health_diary_detail_url(date), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listing_all_diaries(self) -> None:
        self._create_diary(self.user)
        self._create_diary(self.user, date=self.today-datetime.timedelta(1))

        res = self.client.get(HEALTH_DIARY_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_retrieve_diary(self) -> None:
        diary = self._create_diary(self.user)
        res = self.client.get(health_diary_detail_url(diary.slug))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], diary.id)

    def test_retreving_given_statistic_success(self) -> None:
        self._create_diary(self.user)
        self._create_diary(self.user, date=self.today-datetime.timedelta(1))

        statistic_name = 'weight'
        res = self.client.get(health_statistic_url(statistic_name))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
