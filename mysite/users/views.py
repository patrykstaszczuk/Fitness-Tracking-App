from rest_framework import status
from rest_framework.authtoken.views import APIView
from rest_framework.response import Response

from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token

from users import services, selectors
from users import serializers

from mysite.exceptions import ApiErrorsMixin
from mysite.renderers import CustomRenderer
from mysite.views import BaseAuthPermClass


class BaseViewClass(BaseAuthPermClass, ApiErrorsMixin, APIView):
    """ base class for all users app views """

    def get_serializer_context(self):
        """ Extra context provided to the serializer class. """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def set_location_in_header(self, request) -> dict:
        """ set location with proper url in header """
        return {'Location': reverse(
            'users:user-profile', request=request)}


class UserCreateApi(ApiErrorsMixin, APIView):
    """ API for creating user """
    renderer_classes = [CustomRenderer, ]

    def set_location_in_header(self, request) -> dict:
        """ set location with proper url in header """
        return {'Location': reverse(
            'users:user-token', request=request)}

    def post(self, request, *args, **kwargs):
        """ create user """

        serializer = serializers.UserInputSerializer(data=request.data)
        if serializer.is_valid():
            user_service = services.UserService(data=serializer.data)
            user_service.validate()
            user_service.create()
            headers = self.set_location_in_header(request=request)
            return Response(status=status.HTTP_201_CREATED, headers=headers)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ObtainTokenView(ApiErrorsMixin, APIView):
    """ API for obtaining token """

    def post(self, request, *args, **kwargs):
        """ generate token for user """
        serializer = serializers.UserTokenInputSerializer(data=request.data)
        if serializer.is_valid():
            user = selectors.user_authenticate(serializer.data)
            token, created = Token.objects.get_or_create(user=user)
            return Response(data={'token': token.key}, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileApi(BaseViewClass):
    """ API for retrieving user profile """

    def get(self, request, *args, **kwargs):
        """ return user profile """
        serializer = serializers.UserOutputSerializer(
            instance=request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserUpdateApi(BaseViewClass):
    """ API for updating user profile """

    def patch(self, request, *args, **kwargs):
        """ update user profile """

        serializer = serializers.UserUpdateInputSerializer(data=request.data)
        if serializer.is_valid():
            user_service = services.UserService(
                user=request.user, data=serializer.data)
            user_service.validate_update_data()
            user = user_service.update()

            headers = self.set_location_in_header(request)
            return Response(status=status.HTTP_200_OK, headers=headers)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserChangePasswordApi(BaseViewClass):
    """ API for updating user password """

    def patch(self, request, *args, **kwargs):
        """ update user password """
        serializer = serializers.UserPasswordInputSerializer(data=request.data)
        if serializer.is_valid():
            user_service = services.UserService(
                user=request.user, data=serializer.data)
            user_service.change_password()
            return Response(status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListGroupApi(BaseViewClass):
    """ API for retrieving user groups """

    def get(self, request, *args, **kwargs):
        """ retrieve user groups """
        user_groups = selectors.user_get_groups(user=request.user)
        context = self.get_serializer_context()
        serializer = serializers.UserGroupOutputSerializer(
            user_groups, many=True, context=context)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UserSendGroupInvitationApi(BaseViewClass):
    """ AIP for sending group invitation """

    def post(self, request, *args, **kwargs):
        """ send invitation """
        # in order to maintain consistency I use one field serializer insted of #
        # directly passing data to services #
        serializer = serializers.IdSerializer(data=request.data)
        if serializer.is_valid():
            group_service = services.GroupService(
                user=request.user, data=serializer.data)
            group_service.send_group_invitation()
            return Response(status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAcceptInvitationApi(BaseViewClass):
    """ API for managing group invitations """

    def post(self, request, *args, **kwargs):
        """ accept or deny group invitation """

        serializer = serializers.IdSerializer(data=request.data)
        if serializer.is_valid():
            group_service = services.GroupService(
                user=request.user, data=serializer.data)
            group_service.validate_pending_membership()
            group_service.accept_group_invitation()
            return Response(status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDenyInvitationApi(BaseViewClass):
    """ API for managing group invitations """

    def post(self, request, *args, **kwargs):
        """ accept or deny group invitation """
        serializer = serializers.IdSerializer(data=request.data)
        if serializer.is_valid():
            group_service = services.GroupService(
                user=request.user, data=serializer.data)
            group_service.validate_pending_membership()
            group_service.deny_group_invitation()
            return Response(status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLeaveGroupApi(BaseViewClass):
    """ API for leaving group """

    def post(self, request, *args, **kwargs):
        """ leave given group """
        serializer = serializers.IdSerializer(data=request.data)
        if serializer.is_valid():
            group_service = services.GroupService(
                user=request.user, data=serializer.data)
            group_service.validate_membership()
            group_service.leave_group()
            return Response(status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
