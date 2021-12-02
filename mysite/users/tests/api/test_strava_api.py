from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
import time
from users import selectors


class StravaApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.auth_user = get_user_model().objects.create_user(
            email='test@gmail.com',
            name='auth_user',
            password='testpass'
        )
        self.client.force_authenticate(self.auth_user)

    @patch('users.services.strava_services.authorize_to_strava')
    @patch('users.selectors.strava_selectors.has_needed_information_for_request')
    def test_strava_already_associated_with_user(self, mock, mock_validation):
        """ test trying to associate user to strava account,
        when its already done """
        mock_validation.return_value = True
        url = reverse('strava-auth')
        payload = {
            'code': 'accf7a173306f79d9ed09cc08ef0b7b3a5d724c6'
        }
        res = self.client.get(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'Already connected')

    def test_strava_code_not_provided_in_url(self):
        """ test strava code not provided in url """

        url = reverse('strava-auth')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['status'],
                         'No Strava code provided in url or other problem occured. Contact site administrator')

    @patch('users.selectors.process_request')
    def test_associate_user_with_strava(self, mock):
        """ test associating user with strava via provided code in url """
        data = {'expires_at': 123, 'refresh_token': 123,
                'access_token': 123}
        mock.return_value = data
        url = reverse('strava-auth')
        payload = {
            'code': 'accf7a173306f79d9ed09cc08ef0b7b3a5d724c6'
        }
        res = self.client.get(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'Ok')

    @patch('users.selectors.get_strava_last_request_epoc_time')
    @patch('users.selectors.process_request')
    def test_authorize_to_strava_timeout(self, mock_auth, mock_time):
        """ test trying to authorize to strava multile times with wrong code
        implies timeout """

        mock_auth.return_value = {'error': 'error'}
        mock_time.return_value = time.time() - 1
        url = reverse('strava-auth')
        payload = {
            'code': 'wrong code'
        }
        res = self.client.get(url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        for i in range(3):
            res = self.client.get(url, payload)
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(res.data['status'],
                             'To many requests try again soon')

    @patch('users.selectors.get_strava_last_request_epoc_time')
    @patch('users.selectors.process_request')
    def test_authorize_to_strava_after_third_attempt(self, mock_auth, mock_time):
        """ test timeout system works as expected """

        data = {'expires_at': 123, 'refresh_token': 123,
                'access_token': 123}
        mock_auth.return_value = data
        mock_time.side_effect = [
            time.time()-1, time.time()-35, time.time()-3610]

        url = reverse('strava-auth')
        payload = {
            'code': 'wrong code'
        }
        for i in range(2):
            res = self.client.get(url, payload)
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(res.data['status'],
                             'To many requests try again soon')
        res = self.client.get(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.auth_user.strava.refresh_from_db()
        self.assertTrue(
            selectors.has_needed_information_for_request(self.auth_user.strava))
        self.assertEqual(res.data['status'], 'Ok')
