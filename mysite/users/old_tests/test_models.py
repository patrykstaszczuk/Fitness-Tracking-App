
from django.test import TestCase
from rest_framework.response import Response
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from users import models, services, selectors
from health import models as health_models
from health import selectors as health_selectors
import datetime
import time
from unittest.mock import patch, Mock, MagicMock


def sample_user():
    return get_user_model().objects.create_user(
        email='test@gmail.com',
        name='Patryk',
        password='test',
        age=25,
        weight=88,
        height=188,
        gender='Male'
    )


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """ test creating a new user with an email is successful """

        email = "test@gmail.com"
        password = "testpass123"
        age = 25
        gender = 'MALE'
        weight = 30
        height = 188
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            age=age,
            gender=gender,
            weight=weight,
            height=height
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """ test the email for a new user is normalized """
        email = 'test@GMAIL.COM'
        password = 'testpass'
        age = 25
        gender = 'MALE'
        weight = 25
        height = 188
        user = get_user_model().objects.create_user(email=email,
                                                    password=password,
                                                    age=age, gender=gender,
                                                    weight=weight,
                                                    height=height)
        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """ test creating user with no email raises error """

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email=None,
                                                 password="dada",
                                                 age=25, gender='Male',
                                                 weight=88, height=188)

    def test_create_new_superuser(self):
        user = get_user_model().objects.create_superuser(
            email='test@gmail.com',
            password='teste',
            age=25,
            weight=88,
            height=188,
            gender='Male'
        )

        self.assertTrue(user.is_superuser, True)

    def test_string_representation_of_group(self):
        """ test the print group name method """
        user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='Patryk',
            password='test',
            age=25,
            weight=88,
            height=188,
            gender='Male'
        )
        group = models.Group.objects.get(founder=user)
        group_str = group.founder.name + 's group'
        self.assertEqual(str(group), group_str)

    def test_retrieving_avg_health_stats_for_user(self):
        """ test retrieving weekly average stats for user """

        user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='testpass',
            age=25,
            gender='Male',
            weight=25,
            height=188
        )
        avg_weight = 0

        for i in range(1, 8):
            health_models.HealthDiary.objects.create(
                user=user,
                weight=i+70,
                date=datetime.date.today() - datetime.timedelta(days=i+4)
            )
        avg_weight = (71+72+73)/3

        avg_stats = health_selectors.get_weekly_avg_stats(user=user)
        self.assertEqual(avg_stats['weight'], avg_weight)
