
from django.test import TestCase
from rest_framework.response import Response
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from users import models
from health import models as health_models
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
        """ test string representation StravaApi model """

        user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='Patryk',
            password='test',
            age=25,
            weight=88,
            height=188,
            gender='Male'
        )
        obj = models.StravaApi.objects.get(user=user)
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

    @patch('users.models.StravaApi.authorize')
    def test_authorize_to_strava_failed_wrong_response(self, mock):
        """ test authorizing to strava failed with status different than 200
        """
        user = sample_user()
        mock.return_value = Mock(status_code=400, json=lambda: {'error': 'error_message'})
        self.assertEqual(user.authorize_to_strava(code='1234'), False)

    @patch('users.models.StravaApi.authorize')
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

    @patch('users.models.StravaApi.authorize')
    def test_authorize_to_strava_failed_no_needed_info(self, mock):
        """ test authorization failed due to no needed information in strava
        response """

        data = {'ble ble': 123, 'wrong info': 123}
        mock.return_value = MagicMock(spec=HttpResponse, status_code=200,
                                      json=lambda: data)
        user = sample_user()
        self.assertEqual(user.authorize_to_strava(code='1234'), False)

    def test_auth_token_valid_function_failed(self):
        """ test if authentication token is valid """
        user = sample_user()
        self.assertFalse(user.strava.is_token_valid())

    def test_strava_info_valid(self):
        """ test has_needed_informations function when there is stava information availabe"""
        user = sample_user()
        user.strava.access_token = '123',
        user.strava.refresh_token = '123',
        user.strava.expires_at = 123
        self.assertTrue(user.strava.has_needed_informations())

    def test_strava_info_invalid(self):
        """ test has_needed_informations function when there is not strava
        information available"""
        user = sample_user()
        self.assertFalse(user.strava.has_needed_informations())

    @patch('users.models.StravaApi._send_request_to_strava')
    def test_refreshing_token_when_expired(self, mock):
        """ test refreshing token when expired_at time is in past """
        data = {
            'access_token': '321',
            'refresh_token': '543',
            'expires_at': 987
        }
        mock.return_value = MagicMock(status_code=200, json=lambda: data)
        user = sample_user()
        self.assertTrue(user.strava.get_new_strava_access_token())
        self.assertEqual(user.strava.access_token, '321')
        strava_info = models.StravaApi.objects.all()[0]
        self.assertEqual(strava_info.access_token, data['access_token'])
        self.assertEqual(strava_info.refresh_token, data['refresh_token'])
        self.assertEqual(strava_info.expires_at, data['expires_at'])

    @patch('users.models.StravaApi._send_request_to_strava')
    def test_refreshing_token_failed(self, mock):
        """ test refrehsing token when not needed information available in
        db """
        mock.return_value = MagicMock(status_code=400,
                                      json=lambda: {'status': 'error'})
        user = sample_user()
        self.assertFalse(user.strava.get_new_strava_access_token())

    @patch('users.models.StravaApi._send_request_to_strava')
    @patch('users.models.StravaApi.is_token_valid')
    def test_get_list_of_activities_when_token_valid(self, mock_token, mock_send):
        """ test getting list of activities for today """

        data = [
                {
                'id': 1,
                'name': 'test'
                },
                {
                'id': 2,
                'name': 'test2'
                },
            ]

        mock_send.return_value = MagicMock(status_code=200, json=lambda: data)
        mock_token.return_value = True
        today = datetime.date.today()
        user = sample_user()
        res = user.strava.get_strava_activities(today)
        self.assertIn(data[0], res)
        self.assertIn(data[1], res)

    @patch('users.models.StravaApi.get_new_strava_access_token')
    @patch('users.models.StravaApi._send_request_to_strava')
    @patch('users.models.StravaApi.has_needed_informations')
    def test_get_list_of_activities_when_token_invalid(self, mock_valid,
                                                        mock_request,
                                                        mock_token):
        """ test getting list of activities when token is expired """

        user = sample_user()
        data = [
                {
                'id': 1,
                'name': 'test'
                },
                {
                'id': 2,
                'name': 'test2'
                },
            ]
        mock_request.return_value = MagicMock(status_code=200,
                                              json=lambda: data)
        mock_valid.return_value = True
        mock_token.return_value = True
        today = datetime.date.today()
        res = user.strava.get_strava_activities(today)
        self.assertEqual(data, res)

    @patch('users.models.StravaApi.is_token_valid')
    @patch('users.models.StravaApi._send_request_to_strava')
    def test_get_strava_activity(self, mock, mock_token):
        """ test getting information about specific activity """

        activity = {
            'id': 1,
            'name': 'test',
            'calories': 1000
        }
        mock.return_value = MagicMock(status_code=200, json=lambda: activity)
        mock_token.return_value = True
        user = sample_user()

        self.assertEqual(user.strava.get_strava_activity(activity['id']),
                                                         activity)

    def test_process_and_save_strava_activities(self):
        """ test process_and_save_strava_activities function """
        user = sample_user()
        raw_activities = [
            {
                'strava_id': 1,
                'name': 'test',
                'calories': 100,
                'start_date_local': '2018-02-16T06:52:54'
            },
            {
                'strava_id': 2,
                'name': 'test2',
                'calories': 100,
                'start_date_local': '2019-02-16T06:52:54'
            },
            ]
        user.strava.process_and_save_strava_activities(raw_activities)
        activities = models.StravaActivity.objects.filter(user=user)
        self.assertEqual(activities[0].strava_id,
                         raw_activities[0]['strava_id'])
        self.assertEqual(activities[1].strava_id,
                         raw_activities[1]['strava_id'])

    def test_process_and_save_strava_activities_failed_no_list(self):
        """ test processing strava activities when raw_activities is non
        list """
        user = sample_user()
        raw_activities = {
            'strava_id': 1,
            'name': 'test',
            'calories': 100,
            'start_date_local': '2018-02-16T06:52:54'
        }

        user.strava.process_and_save_strava_activities(raw_activities)
        activities = models.StravaActivity.objects.filter(user=user)
        self.assertEqual(len(activities), 0)

    def test_process_and_save_strava_activities_with_key_error(self):
        """ test saving strava acitivities when there is no such key in
        raw_activities, by omiting that value """
        user = sample_user()
        raw_activities_with_no_calories = [
            {
                'strava_id': 1,
                'name': 'test',
                'start_date_local': '2018-02-16T06:52:54'
            },
            {
                'strava_id': 2,
                'name': 'test2',
                'start_date_local': '2019-02-16T06:52:54'
            },
            ]

        user.strava.process_and_save_strava_activities(raw_activities_with_no_calories)
        activities = models.StravaActivity.objects.filter(user=user)
        self.assertEqual(len(activities), 2)

    def test_process_and_save_strava_activities_faild_no_strava_id(self):
        """ test processing and saving strava activiti not possible when
         no strava_id in response """
        user = sample_user()
        activities = [
             {
                 'name': 'test',
                 'start_date_local': '2018-02-16T06:52:54'
             }
             ]

        user.strava.process_and_save_strava_activities(activities)
        activities = models.StravaActivity.objects.filter(user=user)
        self.assertEqual(len(activities), 0)

    def test_strava_activity_str(self):
        """ test string representation of StravaActivity model """
        user = sample_user()

        payload = {
            'user': user,
            'strava_id': 1,
            'name': 'test',
            'calories': 1000
        }
        activity = models.StravaActivity.objects.create(**payload)

        self.assertEqual(str(activity), payload['name'])
