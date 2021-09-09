from rest_framework import generics, authentication, permissions, status, mixins
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from users import models, serializers
from rest_framework.reverse import reverse
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from mysite.renderers import CustomRenderer
from mysite.views import RequiredFieldsResponseMessage, get_serializer_required_fields


class CreateUserView(RequiredFieldsResponseMessage, generics.CreateAPIView):
    """ create a new user in the system """
    serializer_class = serializers.UserSerializer
    renderer_classes = [CustomRenderer, ]

    def get(self, request, *args, **kwargs):
        """ handle get request and extra check if user is authenticated """
        if self.request.user.is_authenticated:
            return self._redirect_to_profile_page()
        self.get_serializer()
        return Response(data=None, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """ hande post request and extra check if user is authenticated """
        if self.request.user.is_authenticated:
            return self._redirect_to_profile_page()
        response = super().create(request, *args, **kwargs)
        response['Location'] = reverse('users:token', request=request)
        return response

    def _redirect_to_profile_page(self):
        """ redirect to profile page """
        headers = {}
        headers['Location'] = reverse('users:profile')
        return Response(data=None, status=status.HTTP_303_SEE_OTHER,
                        headers=headers)


class CreateTokenView(RequiredFieldsResponseMessage, ObtainAuthToken):
    """ create a new auth token for user """
    serializer_class = serializers.AuthTokenSerializer
    renderer_classes = [CustomRenderer, ]

    def post(self, request, *args, **kwargs):
        """ add location to response header """
        response = super().post(request, *args, **kwargs)
        response['Location'] = reverse('users:profile', request=request)
        return response

    def get(self, request, *args, **kwargs):
        """ return standard response but in custom format that is initiated
         when accessing get_serializer method """
        self.get_serializer()
        return Response(data=None, status=status.HTTP_200_OK)


class ManageUserView(RequiredFieldsResponseMessage, generics.RetrieveUpdateAPIView):
    """ manage the authenticated user profile page """
    serializer_class = serializers.UserSerializer
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]

    def get_object(self):
        """ retrieve and return authenticated user """
        return self.request.user

    def get_serializer(self, *args, **kwargs):
        """ return serializer with dynamically set fields """
        serializer_class = self.get_serializer_class()
        fields = ('email', 'name', 'age', 'gender', 'height', 'weight')
        kwargs['context'] = self.get_serializer_context()
        kwargs['fields'] = fields
        serializer = serializer_class(*args, **kwargs)
        self._serializer_required_fields = get_serializer_required_fields(serializer)
        return serializer

    def get_renderer_context(self):
        """ return renderer context withh extra links in response """
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
    serializer_class = serializers.UserChangePasswordSerializer
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]

    def get_object(self):
        """ retrieve and return authenticated user """
        return self.request.user

    def update(self, request, *args, **kwargs):
        """ handle update request and return response with location in header
        """
        response = super().update(request, *args, **kwargs)
        response['Location'] = reverse('users:profile', request=request)
        return response

    def get(self, request, *args, **kwargs):
        """ return standard response but in custom format that is initiated
         when accessing get_serializer method """
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

    def get_serializer_class(self):
        """ get specific serializer based on action """
        if self.action == 'send_invitation':
            return serializers.SendInvitationSerializer
        elif self.action == 'manage_invitation':
            return serializers.ManageInvitationSerializer
        return self.serializer_class

    def get_object(self):
        """ get group for requested user. Group is automatically created
        when user is created """
        return get_object_or_404(self.queryset, founder=self.request.user)

    def list(self, request, *args, **kwargs):
        """ return all user's groups or return HTTP 204"""
        user_groups = self.request.user.membership.all()
        if user_groups.exists():
            serializer = self.get_serializer(user_groups, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_renderer_context(self):
        """ return rendered context and add extra informations to response """

        context = super().get_renderer_context()
        availabe_links = [
            {'send-group-invitation': reverse('users:group-send-invitation',
                                              request=self.request)},
            {'groups': reverse('users:group-list', request=self.request)},
            {'manage-invitation': reverse('users:group-manage-invitation',
                                          request=self.request)},
            {'leave-group': reverse('users:group-leave-group',
                                    request=self.request)}
        ]
        links = {}
        if self.action == 'manage_invitation':
            links.update(availabe_links[0])
            links.update(availabe_links[1])
        elif self.action == 'send_invitation':
            links.update(availabe_links[2])
            links.update(availabe_links[1])
        elif self.action == 'leave_group':
            context['required'] = ['id', ]
        else:
            links.update(availabe_links[2])
            links.update(availabe_links[0])
            links.update(availabe_links[3])
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
        """ show invitation or accept pending memberships """

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

        if request.method == 'POST' and request.data:
            serializer = serializers.LeaveGroupSerializer(instance=request.user,
                                                          data=request.data,
                                                          context={'user': request.user})
            if serializer.is_valid():
                serializer.save()
                headers = {'Location': reverse('users:group-list',
                                               request=request)}
                return Response(data=serializer.data, status=status.HTTP_200_OK,
                                headers=headers)
            return Response(data=serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = serializers.LeaveGroupSerializer(instance=request.user,
                                                      context={'user': request.user})
        return Response(data=serializer.data, status=status.HTTP_200_OK)
