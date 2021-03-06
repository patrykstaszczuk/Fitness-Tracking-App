import time

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import generics
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from mysite.renderers import CustomRenderer
from mysite.exceptions import ApiErrorsMixin
from users import selectors as users_selectors
from users import services as users_services


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'account': reverse('users:user-profile', request=request, format=format),
        'fitness': reverse('health:dashboard', request=request, format=format),
        'meals-tracker': reverse('meals_tracker:meal-list', request=request, format=format),
        'food': reverse('recipe:recipe-list', request=request, format=format),
    })


def get_serializer_required_fields(serializer):
    """ return fields names which are required """
    writable_fields = []
    required_fields = []
    for f, v in serializer.get_fields().items():
        field_type = str(type(v))[23:-2]
        if not getattr(v, 'read_only'):
            writable_fields.append({"name": f, "type": field_type})
    return required_fields, writable_fields


class RequiredFieldsResponseMessage(ApiErrorsMixin, generics.GenericAPIView):
    """ create custom init for descendants """

    # def get_serializer(self, *args, **kwargs):
    #     """ set serializers required fields private variable """

    #     serializer_instance = super().get_serializer()
    #     self._serializer_required_fields = get_serializer_required_fields(serializer_instance)
    #     return super().get_serializer(*args, **kwargs)

    def get_renderer_context(self):
        """ add links to response """
        context = super().get_renderer_context()
        try:
            self._serializer_required_fields = get_serializer_required_fields(
                self.serializer_class())
        except (TypeError, AssertionError):
            return context

        if self._serializer_required_fields:
            context['required'] = self._serializer_required_fields[0]
            context['writable'] = self._serializer_required_fields[1]
        app_name = self.request.resolver_match.app_name
        if hasattr(self, 'action') and self.basename is not None:
            if self.action == 'retrieve':
                links = {
                    f'{self.basename}-list': reverse(f'{app_name}:{self.basename}-list',
                                                     request=self.request),
                }
            else:
                links = None
            context['links'] = links
        return context

    def __init__(self, *args, **kwargs):
        self._serializer_required_fields = None
        super().__init__(*args, **kwargs)


class BaseAuthPermClass(APIView):
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]


class StravaCodeApiView(BaseAuthPermClass):
    """ View for retrieving strava code """

    def get(self, request, *args, **kwargs):
        """ get the code from url and return response """

        strava_code = request.query_params.get('code')
        response_message = {
            'status': 'No Strava code provided in url or other problem occured. Contact site administrator'}
        response_status = status.HTTP_400_BAD_REQUEST
        if strava_code:
            if users_selectors.is_auth_to_strava(request.user):
                response_message['status'] = 'Already connected'
                response_status = status.HTTP_200_OK
            else:
                now = time.time()
                hour = 3600
                if now - users_selectors.get_strava_last_request_epoc_time(request.user) < hour:
                    response_message['status'] = 'To many requests try again soon'
                elif users_services.authorize_to_strava(request.user, strava_code):
                    response_message['status'] = 'Ok'
                    response_status = status.HTTP_200_OK
        return Response(data=response_message, status=response_status)


class StravaCheckStatusApi(BaseAuthPermClass):

    def get(self, request, *args, **kwrags):
        has_needed_information = users_selectors.has_needed_information_for_request(
            request.user.strava)
        is_auth_to_strava = users_selectors.is_auth_to_strava(request.user)
        is_token_valid = users_selectors.is_token_valid(request.user.strava)
        can_request_be_send = users_selectors.can_request_be_send(
            request.user.strava)

        return Response(data={
            'has_needed_information': has_needed_information,
            'is_auth_to_strava': is_auth_to_strava,
            'is_token_valid': is_token_valid,
            'can_request_be_send': can_request_be_send,
        }, status=status.HTTP_200_OK)
