from rest_framework import status
from rest_framework.response import Response
from meals_tracker import serializers, selectors, services
from mysite.views import RequiredFieldsResponseMessage, BaseAuthPermClass


class MealsTrackerDeleteApi(BaseAuthPermClass, RequiredFieldsResponseMessage):
    """ API for deleting meal """

    def delete(self, request, *args, **kwargs):
        """ handling delete meal request """
        meal = selectors.meal_get(user=request.user, id=kwargs.get('pk'))
        meal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MealsTrackerListApi(BaseAuthPermClass, RequiredFieldsResponseMessage):
    """ API for listing meals """

    def get(self, request, *args, **kwargs):
        """ return list of meals. If date in GET params,
        return melas for given date, else for today """
        date = request.query_params.get('date')
        meals = selectors.meal_list(user=request.user, date=date)
        serializer = serializers.MealOutputSerializer(meals, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class MealsTrackerCreateApi(BaseAuthPermClass, RequiredFieldsResponseMessage):
    """ API for creating meals """

    def post(self, request, *args, **kwargs):
        """ handle post request """

        serializer = serializers.MealInputSerializer(data=request.data)

        if serializer.is_valid():
            meal = services.meal_post_handler(
                user=request.user, data=serializer.data)
            serializer = serializers.MealOutputSerializer(meal)
            # headers = {}
            # headers['Location'] = reverse(
            #     'meals_tracker:meal-list', request=request)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MealsTrackerUpdateApi(BaseAuthPermClass, RequiredFieldsResponseMessage):
    """ API for updating meals """

    def put(self, request, *args, **kwargs):
        """ handle put request """
        meal_id = kwargs.get('pk')
        serializer = serializers.MealInputSerializer(data=request.data)

        if serializer.is_valid():
            meal = selectors.meal_get(user=request.user, id=meal_id)
            updated_meal = services.meal_put_handler(
                instance=meal, data=serializer.data)
            serializer = serializers.MealOutputSerializer(updated_meal)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        """ return put request """
        meal_id = kwargs.get('pk')
        serializer = serializers.MealInputSerializer(data=request.data)

        if serializer.is_valid():
            meal = selectors.meal_get(user=request.user, id=meal_id)
            updated_meal = services.meal_patch_handler(
                instance=meal, data=serializer.data)
            serializer = serializers.MealOutputSerializer(updated_meal)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MealsAvailableDatesApi(BaseAuthPermClass, RequiredFieldsResponseMessage):
    """ API for retrievin all available dates when meals was saved """

    def get(self, request, *args, **kwargs):
        """ """
        dates = selectors.meal_get_available_dates(user=request.user)
        serializer = serializers.MealDateOutputSerializer(dates, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class MealCategoryApi(BaseAuthPermClass, RequiredFieldsResponseMessage):
    """ view for retrieving available meal categories """

    def get(self, request, *args, **kwargs):
        """ retrieving all available categories """
        all_categories = selectors.meal_category_list()
        serializer = serializers.MealCategoryOutputSerializer(
            all_categories, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
