
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

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
    lookup_field = 'id'

    def perform_create(self, serializer):
        """ create a new object """
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """ return meals only for requested user """
        today = datetime.date.today()
        return self.queryset.filter(user=self.request.user).filter(date=today)
