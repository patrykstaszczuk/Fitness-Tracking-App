from rest_framework import generics, authentication, permissions, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import mixins
from users import models
from users import serializers
from rest_framework.reverse import reverse
from users.serializers import UserSerializer, AuthTokenSerializer, \
                             UserChangePasswordSerializer
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token

from mysite.renderers import CustomRenderer
from mysite.views import RequiredFieldsResponseMessage, get_serializer_required_fields


class CreateUserView(RequiredFieldsResponseMessage, generics.CreateAPIView,
                     ):
    """ Create a new user in the system """
    serializer_class = UserSerializer
    renderer_classes = [CustomRenderer, ]

    def create(self, request, *args, **kwargs):
        """ overide response header """
        response = super().create(request, *args, **kwargs)
        response['Location'] = reverse('users:token', request=request)
        return response

    def get(self, request, *args, **kwargs):
        """ redirect to profile page if token provided and valid """
        if self._check_if_token_provided(request):
            return self._redirect_to_profile_page()
        self.get_serializer()
        return Response(data=None, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """ redirect to profile page if token provided and valid """
        if self._check_if_token_provided(request):
            return self._redirect_to_profile_page()
        return self.create(request, *args, **kwargs)

    def _check_if_token_provided(self, request):
        """ redirect user to profile page when accesing as authenticated
        user """
        token_provided = request.META.get('HTTP_AUTHORIZATION')
        if token_provided:
            token = request.META['HTTP_AUTHORIZATION']
            try:
                token = token.split(" ")
                Token.objects.select_related('user').get(key=token[1])
                return True
            except authentication.Token.DoesNotExist:
                pass
        return False

    def _redirect_to_profile_page(self):
        """ redirect to profile page """
        headers = {}
        headers['Location'] = reverse('users:profile')
        return Response(data=None, status=status.HTTP_303_SEE_OTHER,
                        headers=headers)


class CreateTokenView(RequiredFieldsResponseMessage, ObtainAuthToken):
    """ create a new auth token for user """
    serializer_class = AuthTokenSerializer
    renderer_classes = [CustomRenderer, ]

    def post(self, request, *args, **kwargs):
        """ override response header """
        response = super().post(request, *args, **kwargs)
        response['Location'] = reverse('users:profile', request=request)
        return response

    def get(self, request, *args, **kwargs):
        """ return custom response format based on serializer """
        self.get_serializer()
        return Response(data=None, status=status.HTTP_200_OK)


class ManageUserView(RequiredFieldsResponseMessage,
                      generics.RetrieveUpdateAPIView):
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
        fields = ('email', 'name', 'age', 'gender', 'height', 'weight')
        kwargs['context'] = self.get_serializer_context()
        kwargs['fields'] = fields
        serializer = serializer_class(*args, **kwargs)
        self._serializer_required_fields = get_serializer_required_fields(serializer)
        return serializer

    def get_renderer_context(self):
        """ add links to response """
        context = super().get_renderer_context()
        links = {
            'new-password': reverse('users:password-change', request=self.request),
            'groups': reverse('users:group-list', request=self.request)
        }
        context['links'] = links
        context['required'] = self._serializer_required_fields
        return context


class ChangeUserPasswordView(RequiredFieldsResponseMessage,
                             generics.UpdateAPIView):
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

    def get(self, request, *args, **kwargs):
        """ return custom message format based on serializer """
        self.get_serializer()
        return Response(data=None, status=status.HTTP_200_OK)


class GroupViewSet(RequiredFieldsResponseMessage, GenericViewSet,
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

        links = {}
        if self.action == 'manage_invitation':
            links.update(
                {'send-group-invitation': reverse('users:group-send-invitation',
                                                 request=self.request),
                'groups': reverse('users:group-list', request=self.request)}
            )
        elif self.action == 'send_invitation':
            links.update(
                {'manage-invitation': reverse('users:group-manage-invitation',
                                                 request=self.request),
                'groups': reverse('users:group-list', request=self.request)}
            )
        elif self.action == 'leave_group':
            context['required'] = ['id', ]
        else:
            links.update(
                {'manage-invitation': reverse('users:group-manage-invitation', request=self.request),
                'send-group-invitation': reverse('users:group-send-invitation',
                                                 request=self.request),
                 'leave-group': reverse('users:group-leave-group',
                                                  request=self.request)}
            )
        context['links'] = links


        return context

    @action(methods=['GET', 'POST'], detail=False,
            url_path='send-group-invitation')
    def send_invitation(self, request):
        """ send group invitation to other users """

        if not request.data:
            serializer = self.get_serializer()
            return Response(status=status.HTTP_200_OK)

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

    @action(methods=['GET', 'POST'], detail=False, url_path='leave-group')
    def leave_group(self, request):
        """ leave group """

        error = 'ID must be an Integer'

        if request.data:
            try:
                group_id = int(request.data.pop('id'))
                try:
                    self.request.user.leave_group(group_id)
                except models.Group.DoesNotExist:
                    return Response(data={'id': "No such group in your membership "},
                                    status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response(data={'id': error},
                                status=status.HTTP_400_BAD_REQUEST)
        headers = {}
        headers['Location'] = reverse('users:group-list', request=request)
        return Response(status=status.HTTP_200_OK, headers=headers)
