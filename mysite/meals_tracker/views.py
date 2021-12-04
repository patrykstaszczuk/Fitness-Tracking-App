from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.reverse import reverse

from meals_tracker import serializers, selectors
from mysite.views import BaseAuthPermClass
from mysite.exceptions import ApiErrorsMixin
from meals_tracker.services import (
    CreateMeal,
    CreateMealDto,
    AddRecipesToMealDto,
    AddRecipesToMeal,
    AddIngredientsToMeal,
    AddIngredientsToMealDto,
    UpdateMealRecipeDto,
    UpdateMealRecipe,
    UpdateMealIngredient,
    UpdateMealIngredientDto,
    RemoveRecipeFromMeal,
    RemoveIngredientFromMeal,
    DeleteMeal,
)


class MealsBaseViewClass(BaseAuthPermClass, ApiErrorsMixin, APIView):
    """ Base class providing common methods """

    def get_serializer_context(self):
        """ Extra context provided to the serializer class. """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def _get_object(self) -> None:
        id = self.kwargs.get('pk')
        user = self.request.user
        return selectors.meal_get(user, id)

    def set_location_in_header(self, id: int, request: Request) -> dict:
        return {'Location': reverse(
                'meals_tracker:meal-detail', request=request,
                kwargs={'pk': id})}


class MealsApi(MealsBaseViewClass):
    """ API for retreving meals for given date and creating meals """

    def get(self, request, *args, **kwargs):
        date = request.query_params.get('date')
        meals = selectors.meal_list(user=request.user, date=date)
        serializer = serializers.MealsListSerializer(
            instance=meals, many=True, context=self.get_serializer_context())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        dto = self._prepare_dto(request)
        service = CreateMeal()
        meal = service.create(dto)
        headers = self.set_location_in_header(meal.id, request)
        return Response(status=status.HTTP_201_CREATED, headers=headers)

    def _prepare_dto(self, request: Request) -> CreateMealDto:
        serializer = serializers.MealCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return CreateMealDto(
            user=request.user,
            date=data.get('date'),
            category=data.get('category'),
            recipes=data.get('recipes'),
            ingredients=data.get('ingredients')
        )


class MealsDetailApi(MealsBaseViewClass):
    """ API for retrieving/updating specific meals """

    def get(self, request, *args, **kwargs):
        meal = self._get_object()
        serializer = serializers.MealDetailSerializer(
            meal, context=self.get_serializer_context())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        meal = self._get_object()
        service = DeleteMeal()
        service.delete(meal)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MealsRecipesApi(MealsBaseViewClass):
    """ API for managing meal recipes """

    def get(self, request, *args, **kwargs):
        id = kwargs.get('pk')
        recipes = selectors.meal_get_recipes(user=request.user, id=id)
        serializer = serializers.MealRecipesSerializer(
            recipes, many=True, context=self.get_serializer_context())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        meal = self._get_object()
        dto = self._prepare_dto(request)
        service = AddRecipesToMeal()
        service.add(meal, dto)
        headers = self.set_location_in_header(meal.id, request)
        return Response(status=status.HTTP_200_OK, headers=headers)

    def _prepare_dto(self, request: Request) -> AddRecipesToMealDto:
        serializer = serializers.AddRecipeToMealSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return AddRecipesToMealDto(
            user=request.user,
            recipes=data.get('recipes')
        )


class MealsRecipesDetailApi(MealsBaseViewClass):
    """ API for updating meals recipes """

    def put(self, request, *args, **kwargs):
        meal = self._get_object()
        recipe_portion_id = kwargs.get('recipe_pk')
        recipe_to_be_updated = selectors.meal_get_recipes_detail(
            meal, recipe_portion_id)
        dto = self._prepare_dto(request)
        service = UpdateMealRecipe()
        service.update(recipe_to_be_updated, dto)
        headers = self.set_location_in_header(meal.id, request)
        return Response(status=status.HTTP_200_OK, headers=headers)

    def delete(self, request, *args, **kwargs):
        meal = self._get_object()
        recipe_id = kwargs.get('recipe_pk')
        recipe_to_be_deleted = selectors.meal_get_recipes_detail(
            meal, recipe_id)
        service = RemoveRecipeFromMeal()
        service.remove(recipe_to_be_deleted)
        headers = self.set_location_in_header(meal.id, request)
        return Response(status=status.HTTP_200_OK, headers=headers)

    def _prepare_dto(self, request: Request) -> UpdateMealRecipeDto:
        serializer = serializers.MealRecipeUpdateSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return UpdateMealRecipeDto(
            portion=data.get('portion')
        )


class MealsIngredientsApi(MealsBaseViewClass):
    """ API for managing meal recipes """

    def get(self, request, *args, **kwargs):
        id = kwargs.get('pk')
        ingredients = selectors.meal_get_ingredients(request.user, id)
        serializer = serializers.MealIngredientsSerializer(
            ingredients, many=True, context=self.get_serializer_context())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        meal = self._get_object()
        dto = self._prepare_dto(request)
        service = AddIngredientsToMeal()
        service.add(meal, dto)
        headers = self.set_location_in_header(meal.id, request)
        return Response(status=status.HTTP_200_OK, headers=headers)

    def _prepare_dto(self, request: Request) -> AddIngredientsToMealDto:
        serializer = serializers.AddIngredientToMealSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return AddIngredientsToMealDto(
            user=request.user,
            ingredients=data.get('ingredients')
        )


class MealsIngredientsDetailApi(MealsBaseViewClass):
    """ API for updating meal ingredients """

    def put(self, request, *args, **kwargs):
        meal = self._get_object()
        ingredient_id = kwargs.get('ingredient_pk')
        meal_ingredient_to_be_updated = selectors.meal_get_ingredients_detail(
            meal, ingredient_id)
        dto = self._prepare_dto(request)
        service = UpdateMealIngredient()
        service.update(meal_ingredient_to_be_updated, dto)
        headers = self.set_location_in_header(meal.id, request)
        return Response(status=status.HTTP_200_OK, headers=headers)

    def delete(self, request, *args, **kwargs):
        meal = self._get_object()
        id = kwargs.get('ingredient_pk')
        ingredient_to_be_deleted = selectors.meal_get_ingredients_detail(
            meal, id)
        service = RemoveIngredientFromMeal()
        service.remove(ingredient_to_be_deleted)
        headers = self.set_location_in_header(meal.id, request)
        return Response(status=status.HTTP_200_OK, headers=headers)

    def _prepare_dto(self, request: Request) -> UpdateMealIngredientDto:
        serializer = serializers.MealIngredientUpdateSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return UpdateMealIngredientDto(
            unit=data.get('unit'),
            amount=data.get('amount')
        )


class MealsAvailableDatesApi(MealsBaseViewClass):
    """ API for retrievin all available dates when meals was saved """

    def get(self, request, *args, **kwargs):
        """ """
        dates = selectors.meal_get_available_dates(user=request.user)
        serializer = serializers.DatesSerializer(
            dates, many=True, context=self.get_serializer_context())
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class MealCategoryApi(MealsBaseViewClass):
    """ view for retrieving available meal categories """

    def get(self, request, *args, **kwargs):
        """ retrieving all available categories """
        all_categories = selectors.meal_category_list()
        serializer = serializers.MealCategorySerializer(
            all_categories, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
