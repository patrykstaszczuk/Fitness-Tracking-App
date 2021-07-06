from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status

from users import serializers
from users import models

from rest_framework.authtoken.models import Token


CREATE_USER_URL = reverse('users:create')
TOKEN_URL = reverse('users:token')
ME_URL = reverse('users:profile')
PASSWORD_URL = reverse('users:password-change')

GROUP_URL = reverse('users:group-list')


def send_invitation_url():
    return reverse('users:group-send-invitation')


def manage_invitation_url():
    return reverse('users:group-manage-invitation')


def sample_user(email='test2@gmail.com', name='testname2'):
    return get_user_model().objects.create_user(
        email=email,
        password='testpass',
        name=name,
        height=188,
        weight=85,
        age=25,
        sex='Male'
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
            'name': 'testname',
            'height': '185',
            'weight': '85',
            'age': '25',
            'sex': 'Male'
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
            'name': 'testname',
            'height': '185',
            'weight': '85',
            'age': '25',
            'sex': 'Male'
        }

        res = self.client.post(CREATE_USER_URL, payload, foramt='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('location', res._headers)

    def test_create_user_invalid_field_values(self):
        """ test creating user with invalid values in fields """

        payload = {
            'email': 'test@gmail.com',
            'password': 'test',
            'name': 'tes',
            'age': 0,
            'height': 3000,
            'weight': 800

        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_exists(self):
        """ test creating user that already exsists fails """
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'name': 'testname',
            'age': 25,
            'height': 188,
            'weight': 88,
            'sex': 'Male'
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
            'sex': 'Male'
        }
        get_user_model().objects.create_user(**payload)

        res = self.client.post(TOKEN_URL, payload)
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
            'sex': 'Male'
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
            'sex': 'Male'
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
            'sex': self.user.sex,
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
    #          'sex': 'Male'
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
            'sex': 'Male'
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
        self.assertEqual(res.data['pending_membership'][0],
                         serializer.data['id'])

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
