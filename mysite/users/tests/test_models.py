
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

    @patch('users.selectors.get_environ_variables')
    def test_authozie_to_strava_with_no_environ(self, mock):
        """ test authorize_to_strava func failed due to no environ variables
        """
        user = sample_user()
        mock.side_effect = KeyError()
        self.assertEqual(services.authorize_to_strava(user=user, strava_code='1234'), False)

    @patch('users.selectors.process_request')
    def test_authorize_to_strava_failed_wrong_response(self, mock):
        """ test authorizing to strava failed with status different than 200
        """
        user = sample_user()
        mock.return_value = {'error': 'error_message'}
        self.assertEqual(services.authorize_to_strava(user=user, strava_code='1234'), False)

    @patch('users.selectors.process_request')
    def test_authorize_to_strava_func(self, mock):
        """ test authorizing to strava user function """
        data = {'expires_at': 123, 'refresh_token': 123,
                'access_token': 123}
        mock.return_value = data
        user = sample_user()
        self.assertEqual(services.authorize_to_strava(user=user, strava_code='1234'), True)
        user.strava.refresh_from_db()
        self.assertEqual(user.strava.expires_at, 123)
        self.assertEqual(selectors.has_needed_information_for_request(user.strava), True)

    @patch('users.selectors.process_request')
    def test_authorize_to_strava_failed_no_needed_info(self, mock):
        """ test authorization failed due to no needed information in strava
        response """

        data = {'ble ble': 123, 'wrong info': 123}
        mock.return_value = data
        user = sample_user()
        self.assertEqual(services.authorize_to_strava(user=user, strava_code='1234'), False)

    def test_auth_token_valid_function_failed(self):
        """ test if authentication token is valid """
        user = sample_user()
        self.assertFalse(selectors.is_token_valid(user.strava))

    def test_strava_info_valid(self):
        """ test has_needed_informations function when there is stava information availabe"""
        user = sample_user()
        user.strava.access_token = '123',
        user.strava.refresh_token = '123',
        user.strava.expires_at = 123
        self.assertTrue(selectors.has_needed_information_for_request(user.strava))

    def test_strava_info_invalid(self):
        """ test has_needed_informations function when there is not strava
        information available"""
        user = sample_user()
        self.assertFalse(selectors.has_needed_information_for_request(user.strava))

    @patch('users.selectors.process_request')
    def test_refreshing_token_when_expired(self, mock):
        """ test refreshing token when expired_at time is in past """
        data = {
            'access_token': '321',
            'refresh_token': '543',
            'expires_at': 987
        }
        mock.return_value = data
        user = sample_user()
        self.assertTrue(selectors.get_new_strava_access_token(user.strava))
        self.assertEqual(user.strava.access_token, '321')
        strava_info = models.StravaApi.objects.all()[0]
        self.assertEqual(strava_info.access_token, data['access_token'])
        self.assertEqual(strava_info.refresh_token, data['refresh_token'])
        self.assertEqual(strava_info.expires_at, data['expires_at'])

    @patch('users.selectors.process_request')
    def test_refreshing_token_failed(self, mock):
        """ test refrehsing token when not needed information available in
        db """
        mock.return_value = None
        user = sample_user()
        self.assertFalse(selectors.get_new_strava_access_token(user.strava))

    @patch('users.selectors.process_request')
    @patch('users.selectors.is_token_valid')
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

        mock_send.return_value = data
        mock_token.return_value = True
        today = datetime.date.today()
        user = sample_user()
        res = selectors.get_activities_from_strava(user)
        self.assertIn(data[0], res)
        self.assertIn(data[1], res)

    @patch('users.selectors.get_new_strava_access_token')
    @patch('users.selectors.process_request')
    @patch('users.selectors.has_needed_information_for_request')
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
        mock_request.return_value = data
        mock_valid.return_value = True
        mock_token.return_value = True
        today = datetime.date.today()
        res = selectors.get_activities_from_strava(user)
        self.assertEqual(data, res)

    @patch('users.selectors.is_token_valid')
    @patch('users.selectors.process_request')
    def test_get_strava_activity(self, mock, mock_token):
        """ test getting information about specific activity """

        activity = {
            'id': 1,
            'name': 'test',
            'calories': 1000
        }
        mock.return_value = activity
        mock_token.return_value = True
        user = sample_user()

        self.assertEqual(selectors.get_activities_from_strava(user),
                                                         activity)

    @patch('users.selectors.process_request')
    def test_process_and_save_strava_activities(self, mock):
        """ test process_and_save_strava_activities function """
        user = sample_user()
        raw_activities = [
            {
                'id': 1,
                'name': 'test',
                'calories': 100,
                'start_date_local': '2018-02-16T06:52:54'
            },
            {
                'id': 2,
                'name': 'test2',
                'calories': 100,
                'start_date_local': '2019-02-16T06:52:54'
            },
            ]
        mock.side_effect = [raw_activities[0], raw_activities[1]]
        services.process_and_save_strava_activities(user, raw_activities)
        activities = models.StravaActivity.objects.filter(user=user)
        self.assertEqual(activities[0].strava_id,
                         raw_activities[0]['id'])
        self.assertEqual(activities[1].strava_id,
                         raw_activities[1]['id'])

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

        services.process_and_save_strava_activities(user, raw_activities)
        activities = models.StravaActivity.objects.filter(user=user)
        self.assertEqual(len(activities), 0)

    @patch('users.selectors.process_request')
    def test_process_and_save_strava_activities_with_key_error(self, mock):
        """ test saving strava acitivities when there is no such key in
        raw_activities, by omiting that value """
        user = sample_user()
        raw_activities_with_no_calories = [
            {
                'id': 1,
                'name': 'test',
                'start_date_local': '2018-02-16T06:52:54'
            },
            {
                'id': 2,
                'name': 'test2',
                'start_date_local': '2019-02-16T06:52:54'
            },
            ]
        mock.side_effect = [raw_activities_with_no_calories[0],
                            raw_activities_with_no_calories[1]]
        services.process_and_save_strava_activities(user, raw_activities_with_no_calories)
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

        services.process_and_save_strava_activities(user, activities)
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
