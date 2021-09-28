from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


from users.models import Group

USER_CREATE = reverse('users:user-create')
USER_PROFILE_URL = reverse('users:user-profile')
USER_UPDATE_URL = reverse('users:user-update')
USER_GROUP_URL = reverse('users:user-group')
USER_PASSWORD_URL = reverse('users:user-change-password')
USER_SEND_INVITATION = reverse('users:user-send-group-invitation')
USER_LEAVE_GROUP_URL = reverse('users:user-leave-group')
USER_ACCEPT_INVITATION_URL = reverse(
    'users:user-accept-group-invitation')
USER_DENY_INVITATION_URL = reverse(
    'users:user-deny-group-invitation')
TOKEN_URL = reverse('users:user-token')


def sample_user(email: str, name: str) -> get_user_model:
    """ create sample user """
    return get_user_model().objects.create(
        email=email,
        name=name,
    )


class UserApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.auth_user = get_user_model().objects.create(
            email='test@gmail.com',
            name='auth_user',
        )
        self.auth_user.set_password('testpass')
        self.auth_user.save()
        group = Group.objects.create(founder=self.auth_user)
        self.client.force_authenticate(self.auth_user)

    def test_create_user_success(self):
        payload = {
            'name': 'new user',
            'email': 'new@gmail.com',
            'password': 'newpass123',
            'password2': 'newpass123'
        }
        res = APIClient().post(USER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_user_invalid_fields(self):
        payload = {
            'name': 1234,
            'email': 'string',
            'password': 1233,
            'password2': 3456
        }
        res = APIClient().post(USER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_missing_fields(self):
        payload = {
            'name': 'new user',
            'email': 'new@gmail.com',
            'password': 'newpass123',
        }
        res = APIClient().post(USER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_passwords_do_not_match(self):
        payload = {
            'name': 'new user',
            'email': 'new@gmail.com',
            'password': 'newpass123',
            'password2': 'password',
        }
        res = APIClient().post(USER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_email_already_taken(self):
        payload = {
            'name': 'new user',
            'email': self.auth_user.email,
            'password': 'newpass123',
            'password2': 'newpass123',
        }
        res = APIClient().post(USER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_name_already_taken(self):
        payload = {
            'name': self.auth_user.name,
            'email': 'nw2@gmail.com',
            'password': 'newpass123',
            'password2': 'newpass123',
        }
        res = APIClient().post(USER_CREATE, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_for_user(self):
        payload = {
            'email': 'test2@gmail.com',
            'password': 'testpass',
            'name': 'testname',
            'age': 25,
            'height': 188,
            'weight': 55,
            'gender': 'Male'
        }
        get_user_model().objects.create_user(**payload)
        res = APIClient().post(TOKEN_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_create_token_invalid_credentials(self):
        invalid_payload = {'email': 'test@gmail.com', 'password': 'wrong'}
        res = APIClient().post(TOKEN_URL, invalid_payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        res = APIClient().post(TOKEN_URL, {'email': 'one', 'password': ''})
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        def test_retrive_user_unauthorized(self):
            """test  that authentication is reuqired for users """
        res = APIClient().get(USER_PROFILE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_profile_success(self):
        res = self.client.get(USER_PROFILE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], self.auth_user.name)

    def test_update_user_profile(self):
        payload = {
            'email': 'newtest@gmail.com',
            'name': 'testname2',
            'age': 30,
            'gender': 'Female'
        }
        res = self.client.patch(USER_UPDATE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = res._headers['location'][1]
        res = self.client.get(url)
        self.assertEqual(res.data['name'], payload['name'])

    def test_update_user_password_success(self):
        payload = {
            'old_password': 'testpass',
            'new_password': 'newpass2',
            'confirm_password': 'newpass2'
        }
        res = self.client.patch(USER_PASSWORD_URL, payload)
        self.auth_user.refresh_from_db()
        user = get_user_model().objects.get(email=self.auth_user.email)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(user.check_password(payload['new_password']))

    def test_update_user_password_invalid_old_pass(self):
        payload = {
            'old_password': 'wrongpass',
            'new_password': 'newpass2',
            'confirm_password': 'newpass2'
        }
        res = self.client.patch(USER_PASSWORD_URL, payload)
        self.auth_user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_update_invalid_password(self):
        payload = {
            'old_password': 'testpass',
            'new_password': 'newpass2',
            'confirm_password': 'newpass22323'
        }
        res = self.client.patch(USER_PASSWORD_URL, payload)
        self.auth_user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_update_failed_password_to_short(self):
        payload = {
            'old_password': 'testpass',
            'new_password': 'ne',
            'confirm_password': 'ne'
        }
        res = self.client.patch(USER_PASSWORD_URL, payload)
        self.auth_user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_group_success(self):
        res = self.client.get(USER_GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_retrieve_groups_success(self):
        user2 = sample_user('2@gmail.com', 'tst')
        g1 = Group.objects.create(founder=user2)

        self.auth_user.membership.add(g1)
        res = self.client.get(USER_GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(self.auth_user.membership.all().count(), 2)

    def test_retrieve_and_create_group_unauthenticated_user_failed(self):
        """ check if premissions works as expected """
        client2 = APIClient()
        res = client2.get(USER_GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_only_groups_belongs_to_specific_user(self):
        """ test retrieving groups only created by self.user """

        sample_user('2@gmail.com', 'tst')
        res = self.client.get(USER_GROUP_URL)

        user_group = self.auth_user.membership.all()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(user_group), 1)

    def test_sending_invitation_to_other_user(self):
        """ test sending invitation to other user """

        user2 = sample_user('2@gmail.com', 'tst')
        group = Group.objects.get(founder=self.auth_user)
        payload = {
            'ids': [user2.id, ],
        }
        res = self.client.post(USER_SEND_INVITATION, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user2.refresh_from_db()
        self.assertEqual(str(user2.pending_membership.all()[0]),
                         str(group.name))

    def test_sending_invitation_to_multi_users(self):
        """ test sending invitation to more than one user """

        user2 = sample_user('2@gmail.com', 'tst')
        user3 = sample_user('test3@gmail.com', 'test3name')

        group = Group.objects.get(founder=self.auth_user)

        payload = {
              'ids': [user2.id, user3.id],
        }
        res = self.client.post(USER_SEND_INVITATION, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        group.refresh_from_db()
        self.assertEqual(group.pending_membership.all().count(), 2)

    def test_sending_invitation_to_yourself_failed(self):

        payload = {
            'ids': [self.auth_user.id, ]
        }
        res = self.client.post(USER_SEND_INVITATION, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sending_invitation_to_wrong_user_failed(self):
        """ test sening invitation to non existing user """
        user2 = sample_user('2@gmail.com', 'tst')
        payload = {
            'ids': [user2.id, ]
        }
        user2.delete()
        res = self.client.post(USER_SEND_INVITATION, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_show_group_invitation(self):
        """ test listing group ivitation send by other users """

        user2 = sample_user('2@gmail.com', 'tst')
        group = Group.objects.create(founder=user2)
        self.auth_user.pending_membership.add(group)

        res = self.client.get(USER_GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['status'], 'pending')

    def test_listing_joined_groups_in_group_list(self):
        """ test getting all joined groups """

        user2 = sample_user('2@gmail.com', 'tst')
        group = Group.objects.create(founder=user2)
        self.auth_user.membership.add(group)

        res = self.client.get(USER_GROUP_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[1]['status'], 'member')

    def test_accept_group_invitation(self):
        user2 = sample_user('2@gmail.com', 'tst')
        group = Group.objects.create(founder=user2)
        self.auth_user.pending_membership.add(group)
        payload = {
            'ids': [group.id, ],
        }
        res = self.client.post(USER_ACCEPT_INVITATION_URL, payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        pending_invitations = self.auth_user.pending_membership.all()
        membership = self.auth_user.membership.all()
        self.assertFalse(pending_invitations)
        self.assertEqual(len(membership), 2)

    def test_joining_to_group_without_invitation_failed(self):
        user2 = sample_user('2@gmail.com', 'tst')
        group = Group.objects.create(founder=user2)

        payload = {
            'ids': [group.id, ],
        }
        res = self.client.post(USER_ACCEPT_INVITATION_URL, payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        membership = self.auth_user.membership.all()
        self.assertEqual(len(membership), 1)

    def test_denying_group_invitation(self):
        user2 = sample_user('2@gmail.com', 'tst')
        group = Group.objects.create(founder=user2)
        self.auth_user.pending_membership.add(group)
        payload = {
            'ids': [group.id, ],
        }
        res = self.client.post(USER_DENY_INVITATION_URL, payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        pending_invitations = self.auth_user.pending_membership.all()
        membership = self.auth_user.membership.all()
        self.assertFalse(pending_invitations)
        self.assertEqual(len(membership), 1)

    def test_denying_group_invitation_without_invitation_failed(self):
        user2 = sample_user('2@gmail.com', 'tst')
        group = Group.objects.create(founder=user2)

        payload = {
            'ids': [group.id, ],
        }
        res = self.client.post(USER_DENY_INVITATION_URL, payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        membership = self.auth_user.membership.all()
        self.assertEqual(len(membership), 1)

    def test_leave_group(self):
        user2 = sample_user('2@gmail.com', 'tst')
        group = Group.objects.create(founder=user2)
        self.auth_user.membership.add(group)

        payload = {
            'ids': [group.id, ],
        }
        res = self.client.post(USER_LEAVE_GROUP_URL, payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.auth_user.membership.all()), 1)

    def test_leaving_own_group_failed(self):
        group = self.auth_user.own_group
        payload = {
            'ids': [group.id, ],
        }
        res = self.client.post(USER_LEAVE_GROUP_URL, payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(self.auth_user.membership.all()), 1)

    def test_leaving_non_existing_group_failed(self):
        group = self.auth_user.own_group
        payload = {
            'ids': [group.id, ],
        }
        group.delete()
        res = self.client.post(USER_LEAVE_GROUP_URL, payload,
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(self.auth_user.membership.all()), 0)
