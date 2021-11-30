from rest_framework import status
from rest_framework.response import Response
from meals_tracker import serializers, selectors, services
from mysite.views import RequiredFieldsResponseMessage, BaseAuthPermClass
from rest_framework.views import APIView
from django.urls import reverse
from mysite.exceptions import ApiErrorsMixin


class MealsTrackerBaseViewClass(BaseAuthPermClass, ApiErrorsMixin, APIView):
    """ Base class providing common methods """

    def get_serializer_context(self):
        """ Extra context provided to the serializer class. """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }


class MealsTrackerApi(MealsTrackerBaseViewClass):
    """ API for retreving meals for given date and creating meals """

    def post(self, request, *args, **kwargs):
        headers = {}
        return Response(status=status.HTTP_201_CREATED, headers=headers)


class MealsTrackerDeleteApi(BaseAuthPermClass, RequiredFieldsResponseMessage):
    """ API for deleting meal """

    def delete(self, request, *args, **kwargs):
        """ handling delete meal request """
        meal = selectors.meal_get(user=request.user, id=kwargs.get('pk'))
        meal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MealsTrackerListApi(MealsTrackerBaseViewClass):
    """ API for listing meals """

    def get(self, request, *args, **kwargs):
        """ return list of meals. If date in GET params,
        return melas for given date, else for today """
        date = request.query_params.get('date')
        meals = selectors.meal_list(user=request.user, date=date)
        context = self.get_serializer_context()
        serializer = serializers.MealOutputSerializer(
            meals, many=True, context=context)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class MealsTrackerCreateApi(MealsTrackerBaseViewClass):
    """ API for creating meals """

    def post(self, request, *args, **kwargs):
        """ handle post request """

        serializer = serializers.MealCreateInputSerializer(data=request.data)

        if serializer.is_valid():
            meal_service = services.MealService(
                user=request.user, data=serializer.data)
            meal = meal_service.create()
            headers = {}
            headers.update({'location': reverse('meals_tracker:meal-list')})
            return Response(status=status.HTTP_201_CREATED, headers=headers)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MealsTrackerUpdateApi(MealsTrackerBaseViewClass):
    """ API for updating meals """

    def put(self, request, *args, **kwargs):
        """ handle put request """
        request = self.request
        meal_id = kwargs.get('pk')
        partial = kwargs.get('partial')
        meal = selectors.meal_get(user=request.user, id=meal_id)

        if partial:
            serializer = serializers.MealUpdateInputSerializer(
                data=request.data)
        else:
            serializer = serializers.MealCreateInputSerializer(
                data=request.data)
        if serializer.is_valid():
            kwargs = {'instance': meal, 'partial': partial}
            meal_service = services.MealService(
                user=request.user, data=serializer.data, kwargs=kwargs)
            meal = meal_service.update()
            headers = {}
            headers.update({'location': reverse('meals_tracker:meal-list')})
            return Response(status=status.HTTP_200_OK, headers=headers)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        """ handle patch reqest. Set partial as true and return put request """
        kwargs.update({'partial': True})
        return self.put(request, *args, **kwargs)


class MealsAvailableDatesApi(MealsTrackerBaseViewClass):
    """ API for retrievin all available dates when meals was saved """

    def get(self, request, *args, **kwargs):
        """ """
        dates = selectors.meal_get_available_dates(user=request.user)
        serializer = serializers.MealDateOutputSerializer(dates, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class MealCategoryApi(MealsTrackerBaseViewClass):
    """ view for retrieving available meal categories """

    def get(self, request, *args, **kwargs):
        """ retrieving all available categories """
        all_categories = selectors.meal_category_list()
        serializer = serializers.MealCategoryOutputSerializer(
            all_categories, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
