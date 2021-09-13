from rest_framework import viewsets, mixins, status, authentication, permissions, generics
from rest_framework.decorators import action, api_view, \
    authentication_classes, permission_classes

from rest_framework.response import Response
from health import serializers, models
from health import selectors
import datetime
from mysite.renderers import CustomRenderer
from rest_framework.views import APIView
from rest_framework.reverse import reverse

from mysite.views import RequiredFieldsResponseMessage

import re
import time
from rest_framework.exceptions import ValidationError

from . import selectors, services
from users import selectors as users_selectors
from users import services as users_services


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

        bmi = users_selectors.get_bmi(user=request.user)
        return Response(data={'bmi': bmi}, status=status.HTTP_200_OK)

class HealthDiary(RequiredFieldsResponseMessage):
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]
    serializer_class = serializers.HealthDiaryInputSerializer

    def get_serializer(self, *args, **kwargs):
        """ return serializer. Method used by CustomRenderer"""
        if self.action == 'GET':
            return serializers.HealthDiaryOutputSerializer()
        return serializers.HealthDiaryInputSerializer()

    def get(self, request, *args, **kwargs):
        """ return heatlth data for today """
        now = datetime.date.today()
        users_services.update_activities(user=request.user, date=now)
        health_diary_instance = selectors.get_health_diary(user=request.user)
        serializer = serializers.HealthDiaryOutputSerializer(instance=health_diary_instance)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        """ update health data for today """
        serializer = serializers.HealthDiaryInputSerializer(data=request.data)
        if serializer.is_valid():
            today = datetime.date.today()
            instance = selectors.get_health_diary(user=request.user, date=today)
            services.update_health_diary(instance=instance, data=serializer.data)
            serializer = serializers.HealthDiaryOutputSerializer(instance)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_renderer_context(self):
        """ add links to response """

        context = super().get_renderer_context()
        links = {
            'raports': reverse('health:health-list', request=self.request),
            'weekly-summary': reverse('health:weekly-summary',
                                      request=self.request)
        }
        user = self.request.user
        if user.is_authenticated and not users_selectors.is_auth_to_strava(user=user):
            url = 'https://www.strava.com/oauth/authorize?'
            params = [
                'client_id=69302',
                'response_type=code',
                'redirect_uri=http://localhost:8000/strava-auth',
                'approval_prompt=force',
                'scope=activity:read_all'
            ]
            for param in params:
                url += param + '&'
            links.update({"connect-strava": url})
        context['links'] = links
        context['required'] = self._serializer_required_fields
        return context


class HealthRaport(RequiredFieldsResponseMessage, viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    """ View for managing user health statistics history """

    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]
    serializer_class = serializers.HealthDiaryOutputSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        """ filter queryset to requsted user only and exclude today when listing instances """
        today = datetime.date.today()
        if self.action == 'list':
            return selectors.get_health_diaries(user=self.request.user).exclude(date=today)
        return selectors.get_health_diaries(user=self.request.user)

    def list(self, request, *args,   **kwargs):
        """ return list of HealthDiary's objects """
        instances = self.get_queryset()
        serializer = serializers.HealthDiaryOutputSerializer(instances, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """ check whether field name or date was provided as slug and return appropriate data """
        slug = kwargs.get('slug')
        if not re.search("....-..-..", slug):
            field = selectors.map_slug_to_health_diary_field(slug)
            if not field:
                return Response(data={f'{slug} field not allowed as slug'}, status=status.HTTP_400_BAD_REQUEST)
            all_field_values = selectors.get_all_values_for_given_field(request.user, field)
            serializer = serializers.HealthDiaryOutputSerializer(all_field_values, many=True, fields=(field, ))
            if serializer.data:
                return Response(data=serializer.data, status=status.HTTP_200_OK)
            return Response(data=serializer.data, status=status.HTTP_204_NO_CONTENT)
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *arsg, **kwargs):
        """ update instance """

        instance = self.get_object()
        serializer = serializers.HealthDiaryInputSerializer(data=request.data)
        if serializer.is_valid():
            services.update_health_diary(instance, data=serializer.data)
            serializer = serializers.HealthDiaryOutputSerializer(instance)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_renderer_context(self):
        """ add links to response """
        context = super().get_renderer_context()
        approved_fields = selectors.get_fields_allowed_for_calculations()
        links = {}
        for field in approved_fields:
            links.update({f'{field.name}-history':
                          reverse('health:health-detail',
                                  kwargs={'slug': field.name}, request=self.request)})
        context['links'] = links
        context['required'] = self._serializer_required_fields
        return context


class HealthWeeklySummary(APIView):
    """ view for retrieving weekly summary """
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]

    def get(self, request, *args, **kwargs):
        """ retrieve weekly summary """
        weekly_summary = selectors.get_weekly_avg_stats(user=request.user)
        if weekly_summary == {}:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(data=weekly_summary,
                        status=status.HTTP_200_OK)
