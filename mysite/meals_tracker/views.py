
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.reverse import reverse
from meals_tracker import models
from meals_tracker import serializers

import datetime

from mysite.renderers import CustomRenderer


class MealsTrackerViewSet(viewsets.ModelViewSet):
    """ ViewSets for managing meals """

    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]
    serializer_class = serializers.MealsTrackerSerializer
    queryset = models.Meal.objects.all()

    def get_serializer_class(self):
        """ return appriopriate serializer for action """
        if self.action in ['create', 'update', 'partial_update']:
            return serializers.CreateUpdateMealSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """ create a new object """
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """ return meals for specific date """

        # date = self.request.query_params
        # print(date)
        today = datetime.date.today()
        return self.queryset.filter(user=self.request.user).filter(date=today)
