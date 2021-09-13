from rest_framework import generics, authentication, permissions, status, mixins, viewsets
from rest_framework.authtoken.views import ObtainAuthToken, APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from users import models, serializers
from rest_framework.reverse import reverse
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from users import services, selectors
from mysite.exceptions import ApiErrorsMixin
from mysite.renderers import CustomRenderer
from mysite.views import RequiredFieldsResponseMessage, get_serializer_required_fields


class CreateUserView(RequiredFieldsResponseMessage, APIView):
    """ create a new user in the system """
    renderer_classes = [CustomRenderer, ]
    serializer_class = serializers.UserInputSerializer

    def get(self, request, *args, **kwargs):
        """ redirect user when is already authenticated """
        if self.request.user.is_authenticated:
            return self._redirect_to_profile_page()
        return Response(data=None, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """ hande post request and extra check if user is authenticated """
        if self.request.user.is_authenticated:
            return self._redirect_to_profile_page()
        serializer = serializers.UserInputSerializer(data=request.data)
        if serializer.is_valid():
            user = services.create_user(serializer.data)
            serializer = serializers.UserOutputSerializer(user)
            headers = {}
            headers['Location'] = reverse('users:profile')
            return Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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


class ManageUserView(RequiredFieldsResponseMessage, APIView):
    """ manage the authenticated user profile page """
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = serializers.UserInputSerializer
    renderer_classes = [CustomRenderer, ]

    def get(self, request, *args, **kwargs):
        """ retrieve user profile """
        serializer = serializers.UserOutputSerializer(instance=request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        """ handle patch request """

        fields = ('email', 'name', 'age', 'gender', 'height', 'weight')
        kwargs = {}
        kwargs['fields'] = fields
        serializer = serializers.UserInputSerializer(data=request.data, context=kwargs)
        if serializer.is_valid():
            user = services.update_user(user=request.user, data=serializer.data)
            serializer = serializers.UserOutputSerializer(user)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """ map this method to patch """
        return self.patch(request, *args, **kwargs)

    def get_renderer_context(self):
        """ return renderer context withh extra links in response """
        context = super().get_renderer_context()
        links = {
            'new-password': reverse('users:password-change', request=self.request),
            'groups': reverse('users:group-list', request=self.request)
        }
        context['links'] = links
        context['writable'].pop(-1) # pop password and passsowrd2
        context['writable'].pop(-2)
        #context['required'] = self._serializer_required_fields
        return context


class ChangeUserPasswordView(RequiredFieldsResponseMessage):
    """ update user password view """
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = serializers.UserInputSerializer
    renderer_classes = [CustomRenderer, ]

    def patch(self, request, *args, **kwargs):
        """ handle update request and return response with location in header
        """
        fields = ('password', 'password2')
        kwargs = {}
        kwargs['fields'] = fields
        serializer = serializers.UserInputSerializer(data=request.data, context=kwargs)
        if serializer.is_valid():
            services.change_password(user=request.user, data=serializer.data)
            return Response(status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupViewSet(RequiredFieldsResponseMessage, ApiErrorsMixin, viewsets.GenericViewSet, mixins.ListModelMixin):
    """ Manage Group in database """
    serializer_class = serializers.GroupInputSerializer
    renderer_classes = [CustomRenderer, ]
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        """ retrieve reuqested user groups """

        user_groups = selectors.get_membership(user=request.user)

        if user_groups.exists():
            serializer = serializers.GroupOutputSerializer(user_groups, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
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
            serializer = serializers.GroupOutputSerializer()
            return Response(status=status.HTTP_200_OK)
        serializer = serializers.GroupInputSerializer(data=request.data)
        if serializer.is_valid():
            services.send_group_invitation(user=request.user, data=serializer.data)
            return Response(status=status.HTTP_200_OK)
        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET', 'POST'], detail=False, url_path='manage-invitation')
    def manage_invitation(self, request):
        """ show invitation or accept pending memberships """

        if not request.data:
            pending_membership = selectors.get_pending_membership(user=request.user)
            serializer = serializers.GroupOutputSerializer(pending_membership, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        serializer = serializers.GroupInputSerializer(data=request.data)
        if serializer.is_valid():
            services.manage_group_invitation(user=request.user, data=serializer.data)
            return Response(status=status.HTTP_200_OK)
        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET', 'POST'], detail=False, url_path='leave-group')
    def leave_group(self, request):
        """ leave group """

        if not request.data:
            membership = selectors.get_membership(user=request.user)
            serializer = serializers.GroupOutputSerializer(membership, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        else:
            services.leave_group(user=request.user, group_id=request.data)
            return Response(status=status.HTTP_200_OK)