from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework import authentication, permissions
from rest_framework.response import Response
from health import serializers
from health import models
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

    @action(methods=['GET'], detail=False, url_path='podsumowanie-tygodnia')
    def weekly_summary(self, request):
        """ retrievie weekly summary of user health statistics """

        health_statistics_summary = self.request.user.get_weekly_avg_stats()
        return Response(data=health_statistics_summary,
                        status=status.HTTP_200_OK)
