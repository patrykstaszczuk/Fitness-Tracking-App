from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from meals_tracker import models
from meals_tracker import serializers


class MealsTrackerViewSet(viewsets.ModelViewSet):
    """ ViewSets for managing meals """

    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.MealsTrackerSerializer
    queryset = models.Meal.objects.all()

    def get_queryset(self):
        """ return meals only for requested user """
        return self.queryset.filter(user=self.request.user)
