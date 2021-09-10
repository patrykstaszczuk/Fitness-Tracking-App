
from rest_framework import viewsets, mixins, status, authentication, permissions
from rest_framework.decorators import action, api_view, \
    authentication_classes, permission_classes

from rest_framework.response import Response
from health import serializers, models
from health.selectors import get_fields_usable_for_calculations
import datetime
from mysite.renderers import CustomRenderer
from rest_framework.views import APIView
from rest_framework.reverse import reverse

from mysite.views import RequiredFieldsResponseMessage

import re
import time
from rest_framework.exceptions import ValidationError

from . import selectors, services


class Dashboard(APIView):
    """ main view for Health app """
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        """ return possible action for health app """

        data = {
            'bmi': reverse('health:bmi', request=request),
            'daily': reverse('health:health-diary', request=request),
            'raports/': reverse('health:health-list', request=request),
            'weekly-summary/': reverse('health:weekly-summary', request=request),

        }
        return Response(data=data, status=status.HTTP_200_OK)


class BmiViewSet(RequiredFieldsResponseMessage, viewsets.GenericViewSet):
    """ View for retrieving information about BMI from user model """

    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]

    def retrieve(self, request, *args, **kwargs):
        """ retrieve user's BMI """

        bmi = request.user.get_bmi()
        return Response(data={'bmi': bmi}, status=status.HTTP_200_OK)

class HealthDiary(RequiredFieldsResponseMessage):
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]

    def get_serializer(self, *args, **kwargs):
        if self.action == 'GET':
            return serializers.HealthDiaryOutputSerializer()

    def get(self, request, *args, **kwargs):
        """ return heatlth data for today """
        now = datetime.date.today()
        health_diary_instance = selectors.get_health_diaries(user=request.user, date=now)
        serializer = serializers.HealthDiaryOutputSerializer(health_diary_instance, many=False)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        """ update health data for today """
        serializer = serializers.HealthDiaryInputSerializer(data=request.data)
        if serializer.is_valid():
            today = datetime.date.today()
            instance = selectors.get_health_diaries(user=request.user, date=today)
            services.update_health_diary(instance=instance, data=serializer.data)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class HealthDiary(RequiredFieldsResponseMessage, viewsets.GenericViewSet,
#                   mixins.RetrieveModelMixin, mixins.CreateModelMixin,
#                   mixins.UpdateModelMixin):
#     """ view for managing user health diary """

#     authentication_classes = (authentication.TokenAuthentication, )
#     permission_classes = (permissions.IsAuthenticated, )
#     serializer_class = serializers.HealthDiarySerializer
#     renderer_classes = [CustomRenderer, ]

#     def perform_create(self, serializer):
#         """ set instance user to requested user """
#         serializer.save(user=self.request.user)

#     def perform_update(self, serializer):
#         """ set instance user to requested user """
#         serializer.save(user=self.request.user)

#     def get_object(self):
#         """ get or create and return object for requested user """
#         now = datetime.date.today()
#         obj, created = models.HealthDiary.objects.get_or_create(
#             user=self.request.user, date=now)
#         return obj

#     def get_renderer_context(self):
#         """ add links to response """
#         context = super().get_renderer_context()
#         links = {
#             'raports': reverse('health:health-list', request=self.request),
#             'weekly-summary': reverse('health:weekly-summary',
#                                       request=self.request)
#         }
#         user = self.request.user
#         if user.is_authenticated and not user.is_auth_to_strava():
#             url = 'https://www.strava.com/oauth/authorize?'
#             params = [
#                 'client_id=69302',
#                 'response_type=code',
#                 'redirect_uri=http://localhost:8000/strava-auth',
#                 'approval_prompt=force',
#                 'scope=activity:read_all'
#             ]
#             for param in params:
#                 url += param + '&'
#             links.update({"connect-strava": url})
#         context['links'] = links
#         context['required'] = self._serializer_required_fields
#         return context

#     def retrieve(self, request, *args, **kwargs):
#         """ retrieve health objects, download strava activities for given day
#         and save them in database """
#         instance = self.get_object()
#         now = time.time()
#         strava_api_instance = request.user.strava
#         hour = 3600
#         if now - strava_api_instance.get_last_request_epoc_time() > hour:
#             raw_strava_activities = strava_api_instance.get_strava_activities(
#                 date=instance.date)
#             if raw_strava_activities and isinstance(raw_strava_activities, list):
#                 strava_api_instance.process_and_save_strava_activities(
#                     raw_strava_activities)
#         serializer = self.get_serializer(instance)
#         return Response(serializer.data)


class HealthRaport(RequiredFieldsResponseMessage, viewsets.GenericViewSet,
                   mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                   mixins.ListModelMixin):
    """ viewset for managing user health statistic history
    URL mapping: /fitness/daily
                 /fitness/raports
                 /fitness/raports/2021-05-08 e.g ...
                 /fitness/raports/weight e.g

    """
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]
    serializer_class = serializers.HealthRaportSerializer
    queryset = models.HealthDiary.objects.all()
    lookup_field = 'slug'

    def perform_update(self, serializer):
        """ set instance user to requested user """
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        """ return appropriate serializer according to action """
        if self.action in ['retrieve', 'update']:
            return serializers.HealthDiarySerializer
        return self.serializer_class

    def get_queryset(self):
        """ filter queryset to requsted user only """
        today = datetime.date.today()
        if self.action == 'list':
            return self.queryset.filter(user=self.request.user).exclude(date=today)
        return self.queryset.filter(user=self.request.user)

    def retrieve(self, *args, **kwargs):
        """ return appropriate data based on provided slug """

        slug = kwargs.get('slug')
        if not re.search("....-..-..", slug):
            try:
                field = self._map_slug_to_model_field(slug)
            except ValidationError as e:
                return Response(data={'slug': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            instance = self.queryset.filter(user=self.request.user).\
                values(field)
            serializer = serializers.HealthStatisticHistorySerializer(
                instance,
                many=True,
                fields=(field, ),
                context={'request': self.request}
                )
            code = status.HTTP_200_OK
            if not serializer.data:
                code = status.HTTP_204_NO_CONTENT
            return Response(data=serializer.data, status=code)
        return super().retrieve(self, *args, **kwargs)

    def get_renderer_context(self):
        """ add links to response """
        context = super().get_renderer_context()
        approved_fields = get_health_model_usable_fields()
        links = {}
        for field in approved_fields:
            links.update({f'{field.name}-history':
                          reverse('health:health-detail',
                                  kwargs={'slug': field.name}, request=self.request)})
        context['links'] = links
        context['required'] = self._serializer_required_fields
        return context

    def _map_slug_to_model_field(self, field_name):
        """ map verbose name of field to model field name """
        approved_fields = get_health_model_usable_fields()
        for field in approved_fields:
            if field_name in [field.name, field.verbose_name]:
                return field.name
        raise ValidationError(
            "No such field in model approved fields for history viewing")


class HealthWeeklySummary(APIView):
    """ view for retrieving weekly summary """
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]

    def get(self, request, *args, **kwargs):
        """ retrieve weekly summary """
        weekly_summary = request.user.get_weekly_avg_stats()
        if weekly_summary == {}:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(data=weekly_summary,
                        status=status.HTTP_200_OK)
