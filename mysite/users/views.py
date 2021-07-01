from rest_framework import generics, authentication, permissions, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.response import Response
from rest_framework import mixins
from users import models
from users import serializers
from rest_framework.reverse import reverse, reverse_lazy
from users.serializers import UserSerializer, AuthTokenSerializer, \
                             UserChangePasswordSerializer
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token

from mysite.renderers import CustomRenderer


class CreateUserView(generics.CreateAPIView):
    """ Create a new user in the system """
    serializer_class = UserSerializer
    renderer_classes = [CustomRenderer, ]

    def create(self, request, *args, **kwargs):
        """ overide response header """
        response = super().create(request, *args, **kwargs)
        response['Location'] = reverse('users:token', request=request)
        return response


class CreateTokenView(ObtainAuthToken):
    """ create a new auth token for user """
    serializer_class = AuthTokenSerializer
    renderer_classes = [CustomRenderer, ]

    def post(self, request, *args, **kwargs):
        """ override response header """
        response = super().post(request, *args, **kwargs)
        response['Location'] = reverse('users:profile', request=request)
        return response


class ManageUserView(generics.RetrieveUpdateAPIView):
    """ manage the authenticated user """
    serializer_class = UserSerializer
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]

    def get_object(self):
        """ retrieve and return authenticated user """
        return self.request.user

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        fields = ('email', 'name', 'age', 'sex', 'height', 'weight')
        kwargs['context'] = self.get_serializer_context()
        kwargs['fields'] = fields
        return serializer_class(*args, **kwargs)

    def get_renderer_context(self):
        """ add links to response """
        context = super().get_renderer_context()
        links = {
            'new-password': reverse('users:password-change', request=self.request),
            'groups': reverse('users:group-list', request=self.request)
        }
        context['links'] = links
        return context


class ChangeUserPasswordView(generics.UpdateAPIView):
    """ update user password view """
    serializer_class = UserChangePasswordSerializer
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]

    def get_object(self):
        """ retrieve and return authenticated user """
        return self.request.user

    def update(self, request, *args, **kwargs):
        """ override response location """
        response = super().update(request, *args, **kwargs)
        response['Location'] = reverse('users:profile', request=request)
        return response


class GroupViewSet(GenericViewSet, mixins.UpdateModelMixin,
                   mixins.ListModelMixin):
    """ Manage Group in database """
    queryset = models.Group.objects.all()
    serializer_class = serializers.GroupSerializer
    renderer_classes = [CustomRenderer, ]
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

    def get_renderer_context(self):
        """ add links to response """
        context = super().get_renderer_context()
        links = {
            'manage-invitation': reverse('users:group-manage-invitation', request=self.request),
            'send-group-invitation': reverse('users:group-send-invitation',
                                             request=self.request)
        }
        context['links'] = links
        return context

    @action(methods=['POST'], detail=False,
            url_path='send-group-invitation')
    def send_invitation(self, request):
        """ send group invitation to other users """

        group = self.get_object()
        serializer = self.get_serializer(group, request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET', 'POST'], detail=False, url_path='manage-invitation')
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
