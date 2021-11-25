from .base_views import BaseViewClass
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework import status
from recipe import serializers, selectors
from recipe.models import Ingredient
from recipe.services import (
    AddingTagsToIngredientInputDto,
    RemoveTagsFromIngredientInputDto,
    CreateIngredientServiceDto,
    CreateIngredient,
    UpdateIngredient,
    UpdateIngredientServiceDto,
    DeleteIngredient,
    AddTagsToIngredient,
    RemoveTagsFromIngredient,
    MappingUnitDto,
    MapUnitToIngredient,
)


class BaseIngredientClass(BaseViewClass):

    def _get_object(self) -> Ingredient:
        """ return ingredient object """
        slug = self.kwargs.get('slug')
        return selectors.ingredient_get(slug)

    def _set_location_in_header(self, request: Request, slug: str) -> dict:
        return {'Location': reverse(
                'recipe:ingredient-detail', request=request,
                kwargs={'slug': slug})}


class IngredientsApi(BaseIngredientClass):
    """ API for retreving ingredients and creating new ones """

    def get(self, request, *args, **kwargs):
        """ retreving list of ingredients """
        ingredients = selectors.ingredient_list()
        serializer = serializers.IngredientListOutputSerializer(
            ingredients, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """ creating ingredient """

        dto = self._prepare_dto(request)
        service = CreateIngredient()
        ingredient = service.create(dto)
        headers = self._set_location_in_header(request, ingredient.slug)
        return Response(status=status.HTTP_201_CREATED, headers=headers)

    def _prepare_dto(self, request: Request) -> CreateIngredientServiceDto:
        serializer = serializers.IngredientInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return CreateIngredientServiceDto(
            user=request.user,
            ready_meal=data.get('ready_meal'),
            name=data.get('name'),
            calories=data.get('calories'),
            proteins=data.get('proteins'),
            carbohydrates=data.get('carbohydrates'),
            fats=data.get('fats'),
            type=data.get('type'),
            fiber=data.get('fiber'),
            sodium=data.get('sodium'),
            potassium=data.get('potassium'),
            calcium=data.get('calcium'),
            iron=data.get('iron'),
            magnesium=data.get('magnesium'),
            selenium=data.get('selenium'),
            zinc=data.get('zinc')
        )


class IngredientDetailApi(BaseIngredientClass):
    """ API for handling ingredient detail """

    def get(self, request, *args, **kwargs):
        """ handling get request """
        ingredient = self._get_object()
        serializer = serializers.IngredientDetailOutputSerializer(
            ingredient)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """ updating ingredient """
        ingredient = self._get_object()
        dto = self._prepare_dto(request)
        service = UpdateIngredient()
        ingredient = service.update(ingredient, dto)
        headers = self._set_location_in_header(request, ingredient.slug)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """ remove ingredient """
        ingredient = self._get_object()
        service = DeleteIngredient()
        service.delete(ingredient)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _prepare_dto(self, request: Request) -> UpdateIngredientServiceDto:
        serializer = serializers.IngredientInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return UpdateIngredientServiceDto(
            user=request.user,
            ready_meal=data.get('ready_meal'),
            name=data.get('name'),
            calories=data.get('calories'),
            proteins=data.get('proteins'),
            carbohydrates=data.get('carbohydrates'),
            fats=data.get('fats'),
            type=data.get('type'),
            fiber=data.get('fiber'),
            sodium=data.get('sodium'),
            potassium=data.get('potassium'),
            calcium=data.get('calcium'),
            iron=data.get('iron'),
            magnesium=data.get('magnesium'),
            selenium=data.get('selenium'),
            zinc=data.get('zinc')
        )


class IngredientTagsApi(BaseIngredientClass):

    def get(self, request, *args, **kwargs):
        """ return all tags for given ingredient """
        ingredient = self._get_object()
        tags = selectors.ingredient_get_tags(ingredient)
        serializer = serializers.TagOutputSerializer(tags, many=True)
        if serializer.data:
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        """ batch addition tags to ingredient """
        ingredient = self._get_object()
        dto = self._prepare_dto(request)
        service = AddTagsToIngredient()
        service.add(ingredient, dto)
        headers = self._set_location_in_header(request, ingredient.slug)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """ batch removal of ingredient tags """
        ingredient = self._get_object()
        dto = self._prepare_dto(request)
        service = RemoveTagsFromIngredient()
        service.remove(ingredient, dto)
        headers = self._set_location_in_header(request, ingredient.slug)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def _prepare_dto(self, request: Request) -> AddingTagsToIngredientInputDto:
        serializer = serializers.TagsIdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        if request.method == 'POST':
            return AddingTagsToIngredientInputDto(
                user=request.user,
                tag_ids=data.get('tag_ids')
            )
        else:
            return RemoveTagsFromIngredientInputDto(
                tag_ids=data.get('tag_ids')
            )


class IngredientUnitsApi(BaseIngredientClass):

    def get(self, reqeust, *args, **kwargs):
        """ return all units for given ingredient """
        ingredient = self._get_object()
        units = selectors.ingredient_get_units(ingredient)
        serializer = serializers.UnitOutputSerializer(units, many=True)
        if serializer.data:
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        """ create ingredient - unit mapping """
        ingredient = self._get_object()
        dto = self._prepare_dto(request)
        service = MapUnitToIngredient()
        service.create(ingredient, dto)
        headers = self._set_location_in_header(request, ingredient.slug)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def _prepare_dto(reqeust: Request) -> MappingUnitDto:
        serializer = serializers.IngredientUnitSerializer(data=reqeust.data)
        serializer.is_valid(raise_exceptio=True)
        data = serializer.data
        return MappingUnitDto(
            unit=data.get('unit'),
            grams_in_one_unit=data.get('grams')
        )
