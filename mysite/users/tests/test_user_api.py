from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from users import serializers
from users import models


CREATE_USER_URL = reverse('users:create')
TOKEN_URL = reverse('users:token')
ME_URL = reverse('users:profile')
PASSWORD_URL = reverse('users:password_change')

GROUP_URL = reverse('users:group-list')


def send_invitation_url(group_id):
    return reverse('users:group-send-invitation', args=[group_id])


def manage_invitation_url():
    return reverse('users:group-manage-invitation')


def sample_user():
    return get_user_model().objects.create_user(
        email='test2@gmail.com',
        password='testpass',
        name='testname2',
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
            'age': 25,
            'sex': 'Male'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))

        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """ test creating user that already exsists fails """
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'name': 'testname',
            'age': 25,
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
            'sex': self.user.sex
        })

    def test_post_not_allowed(self):
        """ test that post is not allowed on the profile url """
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

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

    def test_create_new_group_success(self):
        """ test creating new group by user """
        res = self.client.post(GROUP_URL, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        group = models.Group.objects.get(id=res.data['id'])

        self.assertEqual(group.founder, self.user)
        self.assertEqual(group.members.count(), 1)

    def test_retrieve_group_when_group_does_not_exists(self):
        """ test retrieving group, when user did not create own group
        and does not belong to any group """
        res = self.client.get(GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_retrieve_group_success(self):
        """ test retrieving group created by user """

        models.Group.objects.create(founder=self.user)
        user_groups = self.user.membership.all()
        serializer = serializers.GroupSerializer(user_groups, many=True)
        res = self.client.get(GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_groups_success(self):
        """ test retrieving group created by user and groups he belongs to """
        user2 = get_user_model().objects.create_user(
            email='test2@gmail.com',
            password='testpassword',
            name='test',
            age=25,
            sex='Male'
        )
        g1 = models.Group.objects.create(founder=user2)
        models.Group.objects.create(founder=self.user)

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
        user2 = get_user_model().objects.create_user(
            email='test2@gmail.com',
            password='testpassword',
            name='test',
            age=25,
            sex='Male'
        )

        models.Group.objects.create(founder=user2)
        res = self.client.get(GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_another_group_failed(self):
        """ test creating new group by user failed, if he has one already """

        models.Group.objects.create(founder=self.user)

        res = self.client.post(GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sending_invitation_to_other_user(self):
        """ test sending invitation to other user """

        user2 = sample_user()
        group = models.Group.objects.create(founder=self.user)

        res = self.client.post(send_invitation_url(group.id),
                               {'user': user2.email}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user2.refresh_from_db()

        self.assertEqual(str(user2.pending_membership.all()[0]),
                         str(group.name))

    def test_show_group_invitation(self):
        """ test listing group ivitation send by other users """

        user2 = sample_user()
        group = models.Group.objects.create(founder=user2)
        self.user.pending_membership.add(group)

        serializer = serializers.GroupSerializer(group)
        res = self.client.get(manage_invitation_url())
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_accept_group_invitation(self):
        """ test accepting group invitation send by other users """

        user2 = sample_user()
        group = models.Group.objects.create(founder=user2)
        test = models.Group.objects.get(id=group.id)
        self.user.pending_membership.add(group)
        serializer = serializers.GroupSerializer([group, ], many=True)
        res = self.client.post(manage_invitation_url(), {'pending_membership':
                                                         [group.id, ]},
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.get(GROUP_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

        pending_invitations = self.user.pending_membership.all()
        self.assertFalse(pending_invitations)
