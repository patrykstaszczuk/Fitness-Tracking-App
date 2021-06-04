from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action, api_view, \
    authentication_classes, permission_classes

from rest_framework import authentication, permissions
from rest_framework.response import Response
from health import serializers
from health import models
from health.models import get_health_model_usable_fields
import datetime


class BmiViewSet(viewsets.GenericViewSet):
    """ View for retrieving information about BMI from user model """

    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def retrieve(self, request, *args, **kwargs):
        """ retrieve user's BMI """

        bmi = request.user.get_bmi()
        return Response(data={'bmi': bmi}, status=status.HTTP_200_OK)


class HealthDiary(viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                  mixins.CreateModelMixin, mixins.UpdateModelMixin):
    """ view for managing user health diary """

    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = serializers.HealthDiarySerializer

    def perform_create(self, serializer):
        """ set instance user to requested user """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """ set instance user to requested user """
        serializer.save(user=self.request.user)

    def get_object(self):
        """ get or create and return object for requested user """
        now = datetime.date.today()
        try:
            return models.HealthDiary.objects.filter(user=self.request.user). \
                get(date=now)
        except models.HealthDiary.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)


class HealthRaport(viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin, mixins.ListModelMixin):
    """ viewset for managing user health statistic history """

    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
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

    def _map_slug_to_model_field(self, field_name):
        """ map verbose name of field to model field name """
        approved_fields = get_health_model_usable_fields()
        for field in approved_fields:
            if field_name in [field.name, field.verbose_name]:
                return field.name
        return None

    @action(methods=['GET'], detail=True, url_path='historia')
    def statistic(self, request, slug=None):
        """ retrieve specific statistic history """

        field = self._map_slug_to_model_field(self.kwargs.get('slug'))

        if field:
            statistic = self.queryset.filter(user=self.request.user).\
                values(field)

            if statistic:
                serializer = serializers.HealthStatisticHistorySerializer(
                    statistic,
                    many=True,
                    fields=(field, )
                    )
                return Response(data=serializer.data,
                                status=status.HTTP_200_OK)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view()
@authentication_classes([authentication.TokenAuthentication, ])
@permission_classes([permissions.IsAuthenticated, ])
def HealthWeeklySummary(request):
    """ viewset for retrieving weekly summary """

    weekly_summary = request.user.get_weekly_avg_stats()
    if weekly_summary == {}:
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(data=weekly_summary,
                    status=status.HTTP_200_OK)
