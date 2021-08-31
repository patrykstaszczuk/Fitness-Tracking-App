
from django.test import TestCase
from rest_framework.response import Response
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from users import models
from health import models as health_models
import datetime
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
        avg_sleep_length = 0

        for i in range(1, 8):
            health_models.HealthDiary.objects.create(
                user=user,
                weight=i+70,
                sleep_length=i+7,
                date=datetime.date.today() - datetime.timedelta(days=i+4)
            )
        avg_weight = (71+72+73)/3
        avg_sleep_length = (8+9+10)/3

        avg_stats = user.get_weekly_avg_stats()
        self.assertEqual(avg_stats['weight'], avg_weight)
        self.assertEqual(avg_stats['sleep_length'], avg_sleep_length)

    def test_strava_tokens_str_representation(self):
        """ test string representation StravaTokens model """

        user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='Patryk',
            password='test',
            age=25,
            weight=88,
            height=188,
            gender='Male'
        )
        obj = models.StravaTokens.objects.get(user=user)
        obj.expires_at = 1234
        obj.token = '123'
        obj.access_token = '123'
        self.assertEqual(str(obj), str(user) + str(obj.expires_at))

    @patch('users.models.MyUser.get_environ_variables')
    def test_authozie_to_strava_with_no_environ(self, mock):
        """ test authorize_to_strava func failed due to no environ variables
        """
        user = sample_user()
        mock.side_effect = KeyError()
        self.assertEqual(user.authorize_to_strava(code='1234'), False)

    @patch('users.models.StravaTokens.authorize')
    def test_authorize_to_strava_failed_wrong_response(self, mock):
        """ test authorizing to strava failed with status different than 200
        """
        user = sample_user()
        mock.return_value = Mock(status_code=400, json=lambda: {'error': 'error_message'})
        self.assertEqual(user.authorize_to_strava(code='1234'), False)

    @patch('users.models.StravaTokens.authorize')
    def test_authorize_to_strava_func(self, mock):
        """ test authorizing to strava user function """
        data = {'expires_at': 123, 'refresh_token': 123,
                'access_token': 123}
        mock.return_value = MagicMock(spec=Response, status_code=200,
                                      json=lambda: data)
        user = sample_user()
        self.assertEqual(user.authorize_to_strava(code='1234'), True)
        self.assertEqual(user.strava.expires_at, 123)
        self.assertEqual(user.strava.valid, True)

    @patch('users.models.StravaTokens.authorize')
    def test_authorize_to_strava_failed_no_needed_info(self, mock):
        """ test authorization failed due to no needed information in strava
        response """

        data = {'ble ble': 123, 'wrong info': 123}
        mock.return_value = MagicMock(spec=HttpResponse, status_code=200,
                                      json=lambda: data)
        user = sample_user()
        self.assertEqual(user.authorize_to_strava(code='1234'), False)

    def test_auth_token_valid_function(self):
        """ test if authentication token is valid """
        user = sample_user()
        self.assertFalse(user.strava.is_token_valid())

    @patch('users.models.StravaTokens._send_request_to_strava')
    def test_refreshing_token_when_expired(self, mock):
        """ test refreshing token when expired_at time is in past """
        data = {
            'access_token': '321',
            'refresh_token': '543',
            'expires_at': 987
        }
        mock.return_value = MagicMock(status_code=200, json=lambda: data)
        user = sample_user()
        self.assertTrue(user.strava.get_new_token())
        self.assertEqual(user.strava.access_token, '321')
