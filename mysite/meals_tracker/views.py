
from django.shortcuts import render
import json
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.mixins import ListModelMixin
from django.core.exceptions import ValidationError
from meals_tracker import models
from meals_tracker import serializers

import datetime

from mysite.renderers import CustomRenderer
from mysite.views import RequiredFieldsResponseMessage


class MealsTrackerViewSet(RequiredFieldsResponseMessage, viewsets.ModelViewSet):
    """ ViewSets for managing meals """

    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]
    serializer_class = serializers.MealsTrackerSerializer
    queryset = models.Meal.objects.all()

    def get_serializer_class(self, extra_action=False):
        """ return appriopriate serializer for action """

        if extra_action and self.action in ['list', 'retrieve']:
            return serializers.CreateUpdateMealSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return serializers.CreateUpdateMealSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """ create a new object """
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """ return meals for specific date and request user """

        if self.action == 'retrieve':
            return self.queryset.filter(user=self.request.user)
        date = self._get_date()
        if date:
            try:
                date = self._validate_date(date)
            except (ValueError, ValidationError) as e:
                self.query_params_errors.update({"date": str(e)})
                return None
        else:
            date = datetime.date.today()
        return self.queryset.filter(user=self.request.user).filter(date=date)

    def list(self, request, *args, **kwargs):
        """ check if there is an erros in provided query params """
        response = super().list(request, *args, **kwargs)
        if self.query_params_errors:
            return Response(data=self.query_params_errors,
                            status=status.HTTP_400_BAD_REQUEST)
        return response

    def get_renderer_context(self):
        """ add extra info to response """
        context = super().get_renderer_context()
        links = [
            {"today": reverse('meals_tracker:meal-list', request=self.request)},
            {"categories":
                reverse('meals_tracker:categories', request=self.request)},
            {"availabe-dates":
                reverse('meals_tracker:meal-available-dates',
                        request=self.request)}
        ]
        context['links'] = links

        return context

    def _validate_date(self, date):
        """ validate if provided date is in valid format and does not exceed
        today """
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        today = datetime.date.today()
        if date > today:
            raise ValidationError(f"{date} > {today}, you cannot filter by \
                                 future date")
        return date

    def _get_date(self):
        """ get date from query params """
        return self.request.query_params.get('date')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_params_errors = {}

    @action(methods=['GET'], detail=False, url_path='available-dates')
    def available_dates(self, request):
        """ endpoint for retrieving all dates where any meals was provided """

        if request.user:
            dates = models.Meal.objects.filter(user=request.user).values('date')
            serializer = serializers.DatesSerializer(dates, many=True,
                                                     request=request,
                                                     )
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=None, status=status.HTTP_404_NOT_FOUND)


class MealCategoryListView(RequiredFieldsResponseMessage, ListAPIView):
    """ view for retrieving available meal categories """

    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]
    serializer_class = serializers.MealCategorySerializer
    queryset = models.MealCategory.objects.all()
