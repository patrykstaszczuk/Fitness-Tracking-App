from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from users.serializers import UserSerializer, AuthTokenSerializer, \
                             UserChangePasswordSerializer


class CreateUserView(generics.CreateAPIView):
    """ Create a new user in the system """
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """ create a new auth token for user """
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """ manage the authenticated user """
    serializer_class = UserSerializer
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def get_object(self):
        """ retrieve and return authenticated user """
        return self.request.user

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        fields = ('email', 'name', 'age', 'sex')
        kwargs['context'] = self.get_serializer_context()
        kwargs['fields'] = fields
        return serializer_class(*args, **kwargs)


class ChangeUserPasswordView(generics.RetrieveUpdateAPIView):
    """ update user password view """
    serializer_class = UserChangePasswordSerializer
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def get_object(self):
        """ retrieve and return authenticated user """
        return self.request.user
