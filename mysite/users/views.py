from rest_framework import generics, authentication, permissions, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.response import Response
from rest_framework import mixins
from users import models
from users import serializers
from users.serializers import UserSerializer, AuthTokenSerializer, \
                             UserChangePasswordSerializer
from rest_framework.decorators import action


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


class GroupViewSet(GenericViewSet, mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                   mixins.ListModelMixin):
    """ Manage Group in database """
    queryset = models.Group.objects.all()
    serializer_class = serializers.GroupSerializer
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def perform_create(self, serializer):
        serializer.save(founder=self.request.user)

    def get_serializer_class(self):
        """ get specific serializer for specific action """

        if self.action == 'send_invitation':
            return serializers.SendInvitationSerializer
        elif self.action == 'manage_invitation':
            return serializers.ManageInvitationSerializer
        return self.serializer_class

    def get_object(self):
        """ get group for requested user """
        return models.Group.objects.get(founder=self.request.user)

    def list(self, request, *args, **kwargs):
        """ get the user's group name or return status 204, check if users
         belong to specyfic group or has own group
        """

        user_groups = self.request.user.membership.all()
        if user_groups.exists():
            serializer = self.get_serializer(user_groups, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST'], detail=False,
            url_path='wyslij-zaproszenie-do-grupy')
    def send_invitation(self, request):
        """ send group invitation to other users """

        group = self.get_object()
        serializer = self.get_serializer(group, request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET', 'POST'], detail=False, url_path='zaproszenia')
    def manage_invitation(self, request):
        """ show invitation and accept pending memberships """

        if not request.data:
            serializer = self.get_serializer(instance=request.user)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(instance=request.user,
                                         data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)
