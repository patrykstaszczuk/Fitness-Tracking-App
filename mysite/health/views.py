
from rest_framework import viewsets, mixins, status, authentication, permissions
from rest_framework.decorators import action, api_view, \
    authentication_classes, permission_classes

from rest_framework.response import Response
from health import serializers, models
from health.models import get_health_model_usable_fields
import datetime
from mysite.renderers import CustomRenderer
from rest_framework.views import APIView
from rest_framework.reverse import reverse

from mysite.views import RequiredFieldsResponseMessage

import re
from rest_framework.exceptions import ValidationError


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


class HealthDiary(RequiredFieldsResponseMessage, viewsets.GenericViewSet,
                  mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                  mixins.UpdateModelMixin):
    """ view for managing user health diary """

    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = serializers.HealthDiarySerializer
    renderer_classes = [CustomRenderer, ]

    def perform_create(self, serializer):
        """ set instance user to requested user """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """ set instance user to requested user """
        serializer.save(user=self.request.user)

    def get_object(self):
        """ get or create and return object for requested user """
        now = datetime.date.today()
        obj, created = models.HealthDiary.objects.get_or_create(user=self.request.user, date=now)
        return obj

    def get_renderer_context(self):
        """ add links to response """
        context = super().get_renderer_context()
        links = {
            'raports': reverse('health:health-list', request=self.request),
            'weekly-summary': reverse('health:weekly-summary',
                                      request=self.request)
        }
        if not self.request.user.is_auth_to_strava():
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
        context['required'] = self._serializer_fields
        return context


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
        context['required'] = self._serializer_fields
        return context

    def _map_slug_to_model_field(self, field_name):
        """ map verbose name of field to model field name """
        approved_fields = get_health_model_usable_fields()
        for field in approved_fields:
            if field_name in [field.name, field.verbose_name]:
                return field.name
        raise ValidationError("No such field in model approved fields for history viewing")


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
