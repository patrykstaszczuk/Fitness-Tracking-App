from django.test import TestCase
from django.contrib.auth import get_user_model
from health import models
import datetime


class ModelTests(TestCase):
    """ Test Cases for health model testing """

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='testpass',
            name='testpass',
            height=188,
            weight=85,
            age=25,
            sex='Male'
        )

    def test_add_basic_daily_health_data(self):
        """ test adding daily health data to database """

        now = datetime.date.today()

        defaults = {
            'user': self.user,
            'weight': 73.4,
            'sleep_length': 8,
            'rest_heart_rate': 38,
            'calories': 1000,
            'daily_thoughts': 'Some text'
        }

        obj, created = models.HealthDiary.objects. \
            update_or_create({'date': now}, **defaults)

        self.assertTrue(created)
        self.assertEqual(obj.date, now)

    def test_string_representation_of_model(self):
        """ test string representation """

        now = datetime.date.today()

        defaults = {
            'user': self.user,
            'weight': 73.4,
            'sleep_length': 8,
            'rest_heart_rate': 38,
            'calories': 1000,
            'daily_thoughts': 'Some text'
        }

        obj, created = models.HealthDiary.objects. \
            update_or_create({'date': now}, **defaults)
        str_rep = self.user.name + ' ' + str(obj.date)
        self.assertEqual(str_rep, str(obj))
