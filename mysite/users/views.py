from rest_framework import status
from rest_framework.authtoken.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token

from users import services, selectors
from users import serializers

from mysite.exceptions import ApiErrorsMixin
from mysite.renderers import CustomRenderer
from mysite.views import BaseAuthPermClass

from users.services import (
    CreateUserDto,
    CreateUser,
    CreateToken,
    CreateTokenDto,
    UpdateUserProfile,
    UpdateUserProfileDto,
    UpdateUserPassword,
    UpdateUserPasswordDto,
    SendGroupInvitation,
    SendGroupInvitationDto,
    AcceptGroupInvitation,
    AcceptGroupInvitationDto,
    DenyGroupInvitation,
    DenyGroupInvitationDto,
    LeaveGroup,
    LeaveGroupDto,
)


class BaseViewClass(BaseAuthPermClass, ApiErrorsMixin, APIView):
    """ base class for all users app views """

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def set_location_in_header(self, request) -> dict:
        return {'Location': reverse(
            'users:user-profile', request=request)}


class CreateUserApi(ApiErrorsMixin, APIView):
    """ API for creating user """
    renderer_classes = [CustomRenderer, ]

    def set_location_in_header(self, request) -> dict:
        return {'Location': reverse(
            'users:create-token', request=request)}

    def post(self, request, *args, **kwargs):
        dto = self._prepare_dto(request)
        service = CreateUser()
        user = service.create(dto)
        headers = self.set_location_in_header(request)
        return Response(headers=headers, status=status.HTTP_201_CREATED)

    def _prepare_dto(self, request: Request) -> CreateUserDto:
        serializer = serializers.CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return CreateUserDto(
            email=data.get('email'),
            name=data.get('name'),
            password=data.get('password'),
            password2=data.get('password2'),
            age=data.get('age'),
            height=data.get('height'),
            weight=data.get('weight'),
            gender=data.get('gender')
        )


class ObtainTokenView(ApiErrorsMixin, APIView):
    """ API for obtaining token """

    def post(self, request, *args, **kwargs):
        dto = self._prepare_dto(request)
        service = CreateToken()
        token = service.create(dto)
        token = token.key
        return Response(data={'token': token}, status=status.HTTP_201_CREATED)

    def _prepare_dto(self, request: Request) -> CreateTokenDto:
        serializer = serializers.CreateTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return CreateTokenDto(
            email=data.get('email'),
            password=data.get('password')
        )


class UserProfileApi(BaseViewClass):
    """ API for retrieving user profile """

    def get(self, request, *args, **kwargs):
        serializer = serializers.UserOutputSerializer(
            instance=request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UpdateUserApi(BaseViewClass):
    """ API for updating user profile """

    def put(self, request, *args, **kwargs):
        dto = self._prepare_dto(request)
        service = UpdateUserProfile()
        service.update(request.user, dto)
        headers = self.set_location_in_header(request)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def _prepare_dto(self, request: Request) -> UpdateUserProfileDto:
        serializer = serializers.UpdateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return UpdateUserProfileDto(
            email=data.get('email'),
            name=data.get('name'),
            age=data.get('age'),
            height=data.get('height'),
            weight=data.get('weight'),
            gender=data.get('gender')
        )


class ChangeUserPasswordApi(BaseViewClass):
    """ API for updating user password """

    def put(self, request, *args, **kwargs):
        dto = self._prepare_dto(request)
        service = UpdateUserPassword()
        service.update(request.user, dto)
        headers = self.set_location_in_header(request)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def _prepare_dto(self, request: Request) -> UpdateUserPasswordDto:
        serializer = serializers.UpdateUserPasswordSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return UpdateUserPasswordDto(
            old_password=data.get('old_password'),
            password=data.get('new_password'),
            password2=data.get('confirm_password')
        )


class UserListGroupApi(BaseViewClass):
    """ API for retrieving user groups """

    def get(self, request, *args, **kwargs):
        user_groups = selectors.user_get_groups(user=request.user)
        context = self.get_serializer_context()
        serializer = serializers.UserGroupOutputSerializer(
            user_groups, many=True, context=context)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserSendGroupInvitationApi(BaseViewClass):
    """ AIP for sending group invitation """

    def post(self, request, *args, **kwargs):
        dto = self._prepare_dto(request)
        service = SendGroupInvitation()
        service.send(request.user, dto)
        return Response(status=status.HTTP_200_OK)

    def _prepare_dto(self, request: Request) -> SendGroupInvitationDto:
        serializer = serializers.IdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return SendGroupInvitationDto(
            user_id=serializer.data.get('id')
        )


class UserAcceptInvitationApi(BaseViewClass):
    """ API for managing group invitations """

    def post(self, request, *args, **kwargs):
        dto = self._prepare_dto(request)
        service = AcceptGroupInvitation()
        service.send(request.user, dto)
        return Response(status=status.HTTP_200_OK)

    def _prepare_dto(self, request: Request) -> AcceptGroupInvitationDto:
        serializer = serializers.IdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return AcceptGroupInvitationDto(
            group_id=serializer.data.get('id')
        )


class UserDenyInvitationApi(BaseViewClass):
    """ API for managing group invitations """

    def post(self, request, *args, **kwargs):
        dto = self._prepare_dto(request)
        service = DenyGroupInvitation()
        service.send(request.user, dto)
        return Response(status=status.HTTP_200_OK)

    def _prepare_dto(self, request: Request) -> DenyGroupInvitationDto:
        serializer = serializers.IdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return DenyGroupInvitationDto(
            group_id=serializer.data.get('id')
        )


class UserLeaveGroupApi(BaseViewClass):
    """ API for leaving group """

    def post(self, request, *args, **kwargs):
        dto = self._prepare_dto(request)
        service = LeaveGroup()
        service.send(request.user, dto)
        return Response(status=status.HTTP_200_OK)

    def _prepare_dto(self, request: Request) -> LeaveGroupDto:
        serializer = serializers.IdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return LeaveGroupDto(
            group_id=serializer.data.get('id')
        )
