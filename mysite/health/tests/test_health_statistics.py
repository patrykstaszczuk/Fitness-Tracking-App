from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from health import models

from rest_framework import status
from rest_framework.test import APIClient

from users import serializers as user_serializers
from health import serializers as health_serializers

import datetime

USER_DAILY_HEALTH_DASHBOARD = reverse('health:health-diary')

NOW = datetime.date.today()


def sample_user(email='test2@gmail.com', name='test2'):
    """ creating sample user """
    return get_user_model().objects.create_user(
        email=email,
        name=name,
        password='testpass',
        age=25,
        height=188,
        weight=74,
        sex='Male'
    )


class PrivateHealthApiTests(TestCase):
    """ TestCases for health testing """

    def setUp(self):

        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='testname',
            password='testpass',
            age=25,
            height=188,
            weight=74,
            sex='Male'
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_information(self):
        """ test retrieving information about user """

        url = reverse('users:profile')
        res = self.client.get(url)

        serializer = user_serializers.UserSerializer(self.user)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_calculate_user_bmi(self):
        """ test calculating BMI based on user height and weight """

        url = reverse('health:bmi')

        res = self.client.get(url)
        bmi = self.user.get_bmi()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['bmi'], bmi)

    def test_retrieve_user_daily_health_statistics(self):
        """ test retrieving requested user daily health statistics """

        daily_data = models.HealthDiary.objects.create(
            user=self.user,
            calories=1000,
            weight=70,
            sleep_length=8.4
        )

        res = self.client.get(USER_DAILY_HEALTH_DASHBOARD)

        serializer = health_serializers.HealthDiarySerializer(daily_data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_daily_health_statistics_limited_to_user(self):
        """ test retrieving statistics belongs to request user only """
        user2 = sample_user()
        models.HealthDiary.objects.create(user=user2, weight=63)
        data = models.HealthDiary.objects.create(user=self.user, weight=75)

        res = self.client.get(USER_DAILY_HEALTH_DASHBOARD)
        serializer = health_serializers.HealthDiarySerializer(data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieving_health_diary_from_given_day(self):
        """ test retrieving only daily info """

        diary = models.HealthDiary.objects.create(user=self.user, weight=74.2)

        models.HealthDiary.objects.create(user=self.user, date='2021-05-27',
                                          weight=73.2)
        models.HealthDiary.objects.create(user=self.user, date='2021-05-26',
                                          weight=73.9)
        models.HealthDiary.objects.create(user=self.user, date='2021-05-25',
                                          weight=72.3)
        models.HealthDiary.objects.create(user=self.user, date='2021-05-24',
                                          weight=71.9)

        res = self.client.get(USER_DAILY_HEALTH_DASHBOARD)

        serializer = health_serializers.HealthDiarySerializer(diary)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_user_daily_health_statistics(self):
        """ test adding basic statistics """

        payload = {
            'weight': 74.3,
            'daily_thoughts': 'This will be a greate day!'
        }
        res = self.client.post(USER_DAILY_HEALTH_DASHBOARD, payload,
                               format='json')
        daily_data = models.HealthDiary.objects.filter(user=self.user). \
            get(date=datetime.date.today())
        serializer = health_serializers.HealthDiarySerializer(daily_data)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data, serializer.data)

    def test_update_user_daily_health_statistics_with_put(self):
        """ test updating user health statistics """

        daily_data = models.HealthDiary.objects.create(user=self.user,
                                                       weight=74.3,
                                                       sleep_length=6)

        payload = {
            'weight': '75',
            'calories': '1882'
        }

        res = self.client.put(USER_DAILY_HEALTH_DASHBOARD, payload,
                              format='json')
        daily_data.refresh_from_db()
        serializer = health_serializers.HealthDiarySerializer(daily_data)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_update_user_diary_if_already_exists(self):
        """ test updating diary insted of creating new one, reagrdless POST
        request """

        diary = models.HealthDiary.objects.create(user=self.user, weight=74.5)

        payload = {
            'sleep_length': '6',
            'daily_thoughts': 'some text'
        }

        res = self.client.post(USER_DAILY_HEALTH_DASHBOARD, payload,
                               format='json')
        diary.refresh_from_db()
        serializer = health_serializers.HealthDiarySerializer(diary)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data, serializer.data)

    def test_update_user_daily_health_statistics_with_patch(self):
        """ test updating user diary with patch request """

        diary = models.HealthDiary.objects.create(user=self.user, weight=74.5)

        payload = {
            'sleep_length': '8',
            'weight': '75.5',
        }

        res = self.client.patch(USER_DAILY_HEALTH_DASHBOARD, payload,
                                format='json')
        diary.refresh_from_db()
        serializer = health_serializers.HealthDiarySerializer(diary)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_creating_user_daily_health_statistics_with_invalid_values(self):
        """ test updating failed due to invalid values """

        payload = {
            'sleep_length': '1000',
            'weight': '1000',
            'rest_heart_rate': '1000',
            'calories': '2000',
        }

        res = self.client.post(USER_DAILY_HEALTH_DASHBOARD, payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_updating_user_diary_forbidden_fields_failed(self):
        """ test updating user and date failed """

        payload = {
            'user': 'user2',
            'date': '2020-03-30'
        }

        res = self.client.post(USER_DAILY_HEALTH_DASHBOARD, payload,
                               format='json')
        self.assertNotEqual(res.json()['date'], payload['date'])
