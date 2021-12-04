from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from unittest.mock import patch
from rest_framework.authtoken.models import Token

from users.models import Group
from users.services import (
    CreateUserDto,
    CreateUser,
    CreateToken,
    CreateTokenDto,
    UpdateUserProfileDto,
    UpdateUserProfile,
    UpdateUserPasswordDto,
    UpdateUserPassword,
    SendGroupInvitationDto,
    SendGroupInvitation,
    AcceptGroupInvitation,
    AcceptGroupInvitationDto,
    DenyGroupInvitation,
    DenyGroupInvitationDto,
    LeaveGroup,
    LeaveGroupDto,
)


class UserServicesTests(TestCase):

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test100@gmail.com',
            name='testname100',
            password='authpass',
            gender='Male',
            age=25,
            height=188,
            weight=73,
        )

    @staticmethod
    def _create_user(
        email: str = 'test@gmail.com',
        name: str = 'testname',
        password: str = 'testpassword',
        gender: str = 'Male',
        age: int = 20,
        height: int = 180,
        weight: int = 73
    ) -> get_user_model:
        return get_user_model().objects.create_user(
            email=email,
            name=name,
            password=password,
            gender=gender,
            age=age,
            height=height,
            weight=weight,
        )

    def test_CreateUser_service_success(self) -> None:
        dto = CreateUserDto(
            email='test@gmail.com',
            name='testname',
            age=25,
            height=188,
            weight=73,
            gender='Male',
            password='testpass',
            password2='testpass',
        )
        service = CreateUser()
        user = service.create(dto)
        self.assertEqual(user.name, dto.name)

    def test_CreateUser_service_invalid_age(self) -> None:
        with self.assertRaises(ValidationError):
            CreateUserDto(
                email='test@gmail.com',
                name='testname',
                age=321312321,
                height=188,
                weight=73,
                gender='Male',
                password='testpass',
                password2='testpass',
            )

    def test_CreateUser_service_invalid_height(self) -> None:
        with self.assertRaises(ValidationError):
            CreateUserDto(
                email='test@gmail.com',
                name='testname',
                age=15,
                height=-322,
                weight=73,
                gender='Male',
                password='testpass',
                password2='testpass',
            )

    def test_CreateUser_service_invalid_weight(self) -> None:
        with self.assertRaises(ValidationError):
            CreateUserDto(
                email='test@gmail.com',
                name='testname',
                age=16,
                height=188,
                weight=1000,
                gender='Male',
                password='testpass',
                password2='testpass',
            )

    def test_CreateUser_service_invalid_gender(self) -> None:
        with self.assertRaises(ValidationError):
            CreateUserDto(
                email='test@gmail.com',
                name='testname',
                age=15,
                height=188,
                weight=73,
                gender='some other gender',
                password='testpass',
                password2='testpass',
            )

    def test_CreateUser_service_password_does_not_match(self) -> None:
        with self.assertRaises(ValidationError):
            CreateUserDto(
                email='test@gmail.com',
                name='testname',
                age=15,
                height=188,
                weight=73,
                gender='Male',
                password='testpass',
                password2='testpass222',
            )

    def test_CreateUser_service_password_too_short(self) -> None:
        with self.assertRaises(ValidationError):
            CreateUserDto(
                email='test@gmail.com',
                name='testname',
                age=15,
                height=188,
                weight=73,
                gender='Male',
                password='tes',
                password2='tes',
            )

    def test_CreateUser_service_email_already_taken(self) -> None:
        user = self._create_user(email='test@gmail.com')
        with self.assertRaises(ValidationError):
            CreateUserDto(
                email=user.email,
                name='testname',
                age=23,
                height=188,
                weight=73,
                gender='Male',
                password='testpass',
                password2='testpass',
            )

    def test_CreateUser_service_name_already_taken(self) -> None:
        user = self._create_user(email='test@gmail.com')
        with self.assertRaises(ValidationError):
            CreateUserDto(
                email='testo@gmail.com',
                name=user.name,
                age=23,
                height=188,
                weight=73,
                gender='Male',
                password='testpass',
                password2='testpass',
            )

    @patch('users.selectors.user_authenticate')
    def test_CreteToken_service_success(self, mock) -> None:
        user = self._create_user()
        mock.return_value = user
        dto = CreateTokenDto(
            email=user.email,
            password=user.password,
        )
        service = CreateToken()
        token = service.create(dto)
        self.assertEqual(token, Token.objects.get(user=user))

    def test_CreteToken_service_invalid_credentials(self) -> None:
        user = self._create_user()
        dto = CreateTokenDto(
            email='invalid',
            password='invalid',
        )
        service = CreateToken()
        with self.assertRaises(ValidationError):
            service.create(dto)

    def test_UpdateUserProfile_service_success(self) -> None:
        user = self._create_user()
        dto = UpdateUserProfileDto(
            name='testname2'
        )
        service = UpdateUserProfile()
        service.update(user, dto)
        self.assertEqual(user.name, dto.name)

    def test_UpdateUserProfile_email_taken_(self) -> None:
        user2 = self._create_user(email='taken@gmail.com')
        with self.assertRaises(ValidationError):
            UpdateUserProfileDto(
                email=user2.email
            )

    def test_UpdateUserProfile_group_name_should_change(self) -> None:
        user = self._create_user()
        dto = UpdateUserProfileDto(
            name='new_name'
        )
        service = UpdateUserProfile()
        service.update(user, dto)
        user_gorup = Group.objects.get(founder=user)
        self.assertEqual(user_gorup.name, user.name + 'group')

    @patch('users.services.UpdateUserPassword._check_old_password')
    def test_UpdateUserPassowrd_service_success(self, mock) -> None:
        user = self._create_user()
        dto = UpdateUserPasswordDto(
            old_password=user.password,
            password='newpass',
            password2='newpass'
        )
        service = UpdateUserPassword()
        service.update(user, dto)
        self.assertTrue(user.check_password(dto.password))

    def test_UpdateUserPassowrd_service_invalid_old_password(self) -> None:
        user = self._create_user()
        dto = UpdateUserPasswordDto(
            old_password='invalid',
            password='newpass',
            password2='newpass'
        )
        service = UpdateUserPassword()
        with self.assertRaises(ValidationError):
            service.update(user, dto)

    def test_SendGroupInvitation_service_success(self) -> None:
        user2 = self._create_user()
        group = self.user.own_group
        dto = SendGroupInvitationDto(
            user_id=user2.id
        )
        service = SendGroupInvitation()
        service.send(self.user, dto)
        self.assertTrue(user2.pending_membership.filter(id=group.id).exists())

    def test_SendGroupInvitation_service_to_non_existing_user_failed(self) -> None:
        with self.assertRaises(ValidationError):
            SendGroupInvitationDto(
                user_id=1
            )

    def test_SendGroupInvitation_to_yourself_no_action(self) -> None:
        user2 = self._create_user()
        group = self.user.own_group
        dto = SendGroupInvitationDto(
            user_id=self.user.id
        )
        service = SendGroupInvitation()
        service.send(self.user, dto)
        self.assertFalse(
            self.user.pending_membership.filter(id=group.id).exists())

    def test_AcceptGroupInvitation_service_success(self) -> None:
        user2 = self._create_user()
        group = self.user.own_group
        user2.pending_membership.add(group)

        dto = AcceptGroupInvitationDto(
            group_id=group.id
        )
        service = AcceptGroupInvitation()
        service.accept(user2, dto)
        self.assertTrue(group.members.filter(id=user2.id).exists)
        self.assertFalse(user2.pending_membership.filter(id=group.id).exists())

    def test_AcceptGroupInvitation_service_without_invitation_failed(self) -> None:
        user2 = self._create_user()
        group = self.user.own_group
        dto = AcceptGroupInvitationDto(
            group_id=group.id
        )
        service = AcceptGroupInvitation()
        with self.assertRaises(ValidationError):
            service.accept(user2, dto)

    def test_AcceptGroupInvitation_service_invalid_group_id(self) -> None:
        user2 = self._create_user()
        group = self.user.own_group
        dto = AcceptGroupInvitationDto(
            group_id=1
        )
        service = AcceptGroupInvitation()
        with self.assertRaises(ValidationError):
            service.accept(user2, dto)

    def test_DenyGroupInvitatinon_service_success(self) -> None:
        user2 = self._create_user()
        group = self.user.own_group
        user2.pending_membership.add(group)

        dto = DenyGroupInvitationDto(
            group_id=group.id
        )
        service = DenyGroupInvitation()
        service.deny(user2, dto)
        self.assertFalse(group.members.filter(id=user2.id).exists())
        self.assertFalse(user2.pending_membership.filter(id=group.id).exists())

    def test_DenyGroupInvitation_service_invalid_group_id_no_action(self) -> None:
        dto = DenyGroupInvitationDto(
            group_id=1
        )
        service = DenyGroupInvitation()
        service.deny(self.user, dto)

    def test_LeaveGroup_service_success(self) -> None:
        user2 = self._create_user()
        group = self.user.own_group
        user2.membership.add(group)

        dto = LeaveGroupDto(
            group_id=group.id
        )
        service = LeaveGroup()
        service.leave(user2, dto)
        self.assertFalse(user2.membership.filter(id=group.id).exists())

    def test_LeaveGroup_service_leaving_own_group_failed(self) -> None:
        group = self.user.own_group
        dto = LeaveGroupDto(
            group_id=group.id
        )
        service = LeaveGroup()
        with self.assertRaises(ValidationError):
            service.leave(self.user, dto)
            self.assertTrue(self.user.membership.filter(id=group.id).exists())
