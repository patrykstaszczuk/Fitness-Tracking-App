from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
import time
from users import serializers
from users import models
from unittest.mock import patch, MagicMock


CREATE_USER_URL = reverse('users:create')
TOKEN_URL = reverse('users:token')
ME_URL = reverse('users:profile')
PASSWORD_URL = reverse('users:password-change')

GROUP_URL = reverse('users:group-list')

STRAVA_AUTH_URL = 'https://www.strava.com/oauth/token'


def send_invitation_url():
    return reverse('users:group-send-invitation')


def manage_invitation_url():
    return reverse('users:group-manage-invitation')


def leave_group_url():
    return reverse('users:group-leave-group')


def sample_user(email='test2@gmail.com', name='testname2'):
    return get_user_model().objects.create_user(
        email=email,
        password='testpass',
        name=name,
        height=188,
        weight=85,
        age=25,
        gender='Male'
    )


class PublicUserApiTests(TestCase):
    """ Test the users API (public) """

    def setup(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """ test creating user with valid payload is successfull """
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'password2': 'testpass',
            'name': 'testname',
            'height': '185',
            'weight': '85',
            'age': '25',
            'gender': 'Male'
        }

        res = self.client.post(CREATE_USER_URL, payload, foramt='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))

        self.assertNotIn('password', res.data)

    def test_redirect_to_profile_after_successfull_user_creation(self):
        """ test if response header has location atribute """
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'password2': 'testpass',
            'name': 'testname',
            'height': '185',
            'weight': '85',
            'age': '25',
            'gender': 'Male'
        }

        res = self.client.post(CREATE_USER_URL, payload, foramt='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('location', res._headers)

    def test_create_user_invalid_field_values(self):
        """ test creating user with invalid values in fields """

        payload = {
            'email': 'test@gmail.com',
            'password': 'test',
            'password2': 'test4',
            'name': 'tes',
            'age': 0,
            'height': 3000,
            'weight': 800

        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_passwords_do_not_match(self):
        """ test password confirmation is different then password field """
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'password2': 'testpass2',
            'name': 'testname',
            'height': '185',
            'weight': '85',
            'age': '25',
            'gender': 'Male'
        }

        res = self.client.post(CREATE_USER_URL, payload, foramt='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertNotIn('password', res.data)
        self.assertNotIn('password2', res.data)

    def test_user_exists(self):
        """ test creating user that already exsists fails """
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'name': 'testname',
            'age': 25,
            'height': 188,
            'weight': 88,
            'gender': 'Male'
        }
        get_user_model().objects.create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_for_user(self):
        """ test that a token is created for user """
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'name': 'testname',
            'age': 25,
            'height': 188,
            'weight': 55,
            'gender': 'Male'
        }
        get_user_model().objects.create_user(**payload)

        res = self.client.post(TOKEN_URL, payload)
        print(vars(res))
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """ token is not created with invalid credentials given"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'name': 'testname',
            'age': 25,
            'height': 188,
            'weight': 55,
            'gender': 'Male'
        }
        get_user_model().objects.create_user(**payload)

        invalid_payload = {'email': 'test@gmail.com', 'password': 'wrong'}
        res = self.client.post(TOKEN_URL, invalid_payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """ test that token is not created if user doenst exists """
        payload = {'email': 'test@gmail.com', 'password': 'wrong'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """ test that email and pass are required """
        res = self.client.post(TOKEN_URL, {'email': 'one', 'password': ''})
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrive_user_unauthorized(self):
        """test  that authentication is reuqired for users """

        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """ test API request that required authentication """

    def setUp(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'name': 'testname',
            'age': 25,
            'height': 188,
            'weight': 88,
            'gender': 'Male'
        }
        self.user = get_user_model().objects.create_user(**payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """ test retrieving profile for logged in user """
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name,
            'age': self.user.age,
            'height': self.user.height,
            'weight': self.user.weight,
            'gender': self.user.gender,
        })

    def test_post_not_allowed(self):
        """ test that post is not allowed on the profile url """
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # def test_redirect_to_profile_page_when_access_create_page(self):
    #     """ test redirecting to profile page when already authenticated user
    #      trying to access create new user page """
    #
    #     token = Token.objects.create(key='123456', user=self.user)
    #     res = self.client.get(CREATE_USER_URL, headers={'HTTP_AUTHORIZATION': f'Token {token}'})
    #     self.assertEqual(res.status_code, status.HTTP_303_SEE_OTHER)
    #     self.assertIn('location', res._headers)
    #
    # def test_redirect_to_profile_page_when_access_create_page_post(self):
    #     """ test redirecting authenticated user to profile page when trying
    #      to post on create new user page """
    #
    #     payload = {
    #          'email': 'test@gmail.com',
    #          'password': 'testpass',
    #          'name': 'testname',
    #          'height': '185',
    #          'weight': '85',
    #          'age': '25',
    #          'gender': 'Male'
    #      }
    #
    #     res = self.client.post(CREATE_USER_URL, payload, foramt='json')
    #     self.assertEqual(res.status_code, status.HTTP_303_SEE_OTHER)
    #     self.assertIn('location', res._headers)

    def test_update_user_profile(self):
        """ test updating the user profile for authenticated user """
        payload = {
            'email': 'newtest@gmail.com',
            'name': 'testname',
            'age': 25,
            'gender': 'Male'
        }
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_user_password_success(self):
        """ test updating the user password """
        payload = {
            'old_password': 'testpass',
            'password': 'newpass2',
            'confirm_password': 'newpass2'
        }
        res = self.client.patch(PASSWORD_URL, payload)
        self.user.refresh_from_db()
        user = get_user_model().objects.get(email=self.user.email)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(user.check_password(payload['password']))

    def test_update_user_password_invalid_old_pass(self):
        """ test updating password failed with incorect old
        password provided """
        payload = {
            'old_password': 'wrongpass',
            'password': 'newpass2',
            'confirm_password': 'newpass2'
        }
        res = self.client.patch(PASSWORD_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_update_invalid_password(self):
        """ test updating password failed with no matching confirm password """
        payload = {
            'old_password': 'testpass',
            'password': 'newpass2',
            'confirm_password': 'newpass3'
        }
        res = self.client.patch(PASSWORD_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_update_failed_password_to_short(self):
        """ test updating password failed cause too short """
        payload = {
            'old_password': 'testpass',
            'password': 'newpass',
            'confirm_password': 'newpass'
        }
        res = self.client.patch(PASSWORD_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_group_success(self):
        """ test retrieving group created by user """

        user_groups = self.user.membership.all()
        serializer = serializers.GroupSerializer(user_groups, many=True)
        res = self.client.get(GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_groups_success(self):
        """ test retrieving group created by user and groups he belongs to """
        user2 = sample_user()
        g1 = models.Group.objects.get(founder=user2)

        self.user.membership.add(g1)
        res = self.client.get(GROUP_URL)

        get_user_groups = self.user.membership.all()

        serializer1 = serializers.GroupSerializer(get_user_groups, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer1.data, res.data)
        self.assertEqual(self.user.membership.all().count(), 2)

    def test_retrieve_and_create_group_unauthenticated_user_failed(self):
        """ check if premissions works as expected """

        client2 = APIClient()
        res = client2.get(GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        res = client2.post(GROUP_URL, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_only_groups_belongs_to_specific_user(self):
        """ test retrieving groups only created by self.user """

        sample_user()
        res = self.client.get(GROUP_URL)

        user_group = self.user.membership.all()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(user_group), 1)

    def test_sending_invitation_to_other_user(self):
        """ test sending invitation to other user """

        user2 = sample_user()
        group = models.Group.objects.get(founder=self.user)

        payload = {
            'pending_membership': [user2.id, ],
        }
        res = self.client.post(send_invitation_url(), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user2.refresh_from_db()

        self.assertEqual(str(user2.pending_membership.all()[0]),
                         str(group.name))

    def test_sending_invitation_to_multi_users(self):
        """ test sending invitation to more than one user """

        user2 = sample_user()
        user3 = sample_user(email='test3@gmail.com', name='test3name')

        group = models.Group.objects.get(founder=self.user)

        payload = {
            "pending_membership": [user2.id, user3.id],
        }
        res = self.client.post(send_invitation_url(), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        group.refresh_from_db()

        self.assertEqual(group.pending_membership.all().count(), 2)

    def test_sending_invitation_to_yourself_failed(self):

        payload = {
            'pending_membership': [self.user.id, ]
        }
        res = self.client.post(send_invitation_url(), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sending_invitation_to_wrong_user_failed(self):
        """ test sening invitation to non existing user """

        payload = {
            'pending_membership': [3, ]
        }
        res = self.client.post(send_invitation_url(), payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Taki użytkownik nie istnieje!',
                      res.data['pending_membership'])

    def test_show_group_invitation(self):
        """ test listing group ivitation send by other users """

        user2 = sample_user()
        group = models.Group.objects.get(founder=user2)
        self.user.pending_membership.add(group)

        serializer = serializers.GroupSerializer(group)
        res = self.client.get(manage_invitation_url())
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['data']['pending_membership'][0],
                         serializer.data['id'])

    def test_listing_joined_groups_in_leave_group_endpoint(self):
        """ test getting all joined groups """

        user2 = sample_user()
        group = models.Group.objects.get(founder=user2)
        self.user.membership.add(group)

        res = self.client.get(leave_group_url())
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(group.id, res.json()['data']['groups'][0]['id'])

    def test_accept_group_invitation(self):
        """ test accepting group invitation send by other users """

        user2 = sample_user()
        group = models.Group.objects.get(founder=user2)
        self.user.pending_membership.add(group)
        serializer = serializers.GroupSerializer(group)
        payload = {
            'pending_membership': [group.id, ],
            'action': 1
        }
        res = self.client.post(manage_invitation_url(), payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.get(GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, res.data)

        pending_invitations = self.user.pending_membership.all()
        self.assertFalse(pending_invitations)

    def test_denying_group_invitation(self):
        """ test denying group invitation """

        user2 = sample_user()
        group = models.Group.objects.get(founder=user2)
        self.user.pending_membership.add(group)

        payload = {
            'pending_membership': [group.id, ],
            'action': 0,
        }
        res = self.client.post(manage_invitation_url(), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.pending_membership.all().exists())

    def test_leave_group(self):
        """ test leaving group """

        user2 = sample_user()
        group = models.Group.objects.get(founder=user2)
        self.user.membership.add(group)

        payload = {
            'id': 2
        }
        res = self.client.post(leave_group_url(), {'id': group.id},
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.user.membership.all()), 1)

    def test_leaving_request_user_own_group_failed(self):
        """ test leaving own group failed """

        group = models.Group.objects.get(founder=self.user)
        res = self.client.post(leave_group_url(), {'id': group.id},
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(self.user.membership.all()), 1)

    # def test_retreiving_strava_auth_information(self):
    #     """ test retreving code, tokens and expire date """
    #
    #     url = reverse('strava-auth')
    #
    #     payload = {
    #         'code': 'accf7a173306f79d9ed09cc08ef0b7b3a5d724c6'
    #     }
    #     res = self.client.get(url, payload)
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     self.assertTrue(self.user.strava.access_token)
    #     self.assertTrue(self.user.strava.refresh_token)
    #     self.assertTrue(self.user.strava.expires_at)

    @patch('users.models.MyUser.authorize_to_strava')
    @patch('users.models.StravaApi.is_valid')
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
        self.assertEqual(res.json()['data']['status'], 'Already connected')

    def test_strava_code_not_provided_in_url(self):
        """ test strava code not provided in url """

        url = reverse('strava-auth')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.json()['data']['status'],
                         'No Strava code provided in url or other problem occured. Contact site administrator')

    @patch('users.models.StravaApi.authorize')
    def test_associate_user_with_strava(self, mock):
        """ test associating user with strava via provided code in url """
        data = {'expires_at': 123, 'refresh_token': 123,
                'access_token': 123}
        mock.return_value = MagicMock(status_code=200, json=lambda: data)
        url = reverse('strava-auth')
        payload = {
            'code': 'accf7a173306f79d9ed09cc08ef0b7b3a5d724c6'
        }
        res = self.client.get(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()['data']['status'], 'Ok')
        self.assertTrue(self.user.strava.valid)

    @patch('users.models.StravaApi.get_last_update_time')
    @patch('users.models.StravaApi.authorize')
    def test_authorize_to_strava_timeout(self, mock_auth, mock_time):
        """ test trying to authorize to strava multile times with wrong code
        implies timeout """

        mock_auth.return_value = MagicMock(status_code=400,
                                           json=lambda: {'error': 'error'})
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
            self.assertEqual(res.json()['data']['status'],
                             'To many requests try again soon')

    @patch('users.models.StravaApi.get_last_update_time')
    @patch('users.models.StravaApi.authorize')
    def test_authorize_to_strava_after_third_attempt(self, mock_auth, mock_time):
        """ test timeout system works as expected """

        data = {'expires_at': 123, 'refresh_token': 123,
                'access_token': 123}
        mock_auth.return_value = MagicMock(status_code=200,
                                           json=lambda: data)
        mock_time.side_effect = [time.time()-1, time.time()-35, time.time()-61]

        url = reverse('strava-auth')
        payload = {
            'code': 'wrong code'
        }
        for i in range(2):
            res = self.client.get(url, payload)
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(res.json()['data']['status'],
                             'To many requests try again soon')
        res = self.client.get(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.strava.valid)
        self.assertEqual(res.json()['data']['status'], 'Ok')
