from .base_views import BaseViewClass
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework import status
from recipe import serializers, selectors
from recipe.models import Recipe, Recipe_Ingredient
from users import selectors as users_selectors
from recipe.services import (
    CreateRecipe,
    UpdateRecipe,
    DeleteRecipe,
    CreateRecipeDto,
    AddingTagsInputDto,
    RemoveTagsInputDto,
    AddTagsToRecipe,
    RemoveTagsFromRecipe,
    RecipeIngredientServiceDto,
    AddIngredientsToRecipe,
    RemoveIngredientsFromRecipe,
    UpdateRecipeIngredientDto,
    UpdateRecipeIngredient,
)


class BaseRecipeClass(BaseViewClass):

    def _prepare_recipe_dto_from_validated_data(self, request) -> CreateRecipeDto:
        """ prepare dto for recipe update """
        serializer = serializers.RecipeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return CreateRecipeDto(
            user=self.request.user,
            name=data['name'],
            portions=data['portions'],
            prepare_time=data['prepare_time'],
            description=data['description']
        )

    def _set_location_in_header(self, request, slug):
        return {'Location': reverse(
                'recipe:recipe-detail', request=request,
                kwargs={'slug': slug})}

    def _get_object(self):
        """ return appropriate recipe based on slug """
        slug = self.kwargs.get('slug')
        user = self.request.user
        return selectors.recipe_get(user, slug)


class RecipesApi(BaseRecipeClass):

    def get(self, request, *args, **kwargs):
        """ retrieve list of recipes for authenticated user """
        recipes = selectors.recipe_list(
            user=request.user, filters=request.query_params)
        context = self.get_serializer_context()
        serializer = serializers.RecipeListOutputSerializer(
            recipes, many=True, context=context)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """ handling creation process and return response """
        dto = self._prepare_recipe_dto_from_validated_data(request)
        service = CreateRecipe()
        recipe = service.create(dto)
        headers = self._set_location_in_header(request, recipe.slug)
        return Response(status=status.HTTP_201_CREATED, headers=headers)


class RecipeDetailApi(BaseRecipeClass):
    """ API for retreving recipe detail, updating recipe or deleting recipe """

    def get(self, request, *args, **kwargs) -> Response:
        """ retrive specific recipe based on slug """
        recipe = self._get_object()
        serializer = serializers.RecipeDetailOutputSerializer(
            recipe)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs) -> Response:
        """ handle put request """
        recipe = self._get_object()
        dto = self._prepare_recipe_dto_from_validated_data(request)
        service = UpdateRecipe()
        recipe = service.update(recipe, dto)
        headers = self._set_location_in_header(request, recipe.slug)

        return Response(headers=headers, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs) -> Response:
        recipe = self._get_object()
        service = DeleteRecipe()
        service.delete(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeTagsApi(BaseRecipeClass):
    """ API for managing tags for given recipe """

    def get(self, request, *args, **kwargs):
        """ retreive all tags for given recipe """
        recipe = self._get_object()
        data = selectors.recipe_get_tags(request.user, recipe)
        serializer = serializers.TagOutputSerializer(data, many=True)
        if serializer.data:
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        """ batch addition tags to recipe """
        recipe = self._get_object()
        dto = self._prepare_recipe_tags_dto(request)
        service = AddTagsToRecipe()
        service.add(recipe, dto)
        headers = self._set_location_in_header(request, recipe.slug)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """ batch removal tags from recipe """
        recipe = self._get_object()
        dto = self._prepare_dto(request)
        service = RemoveTagsFromRecipe()
        service.remove(recipe, dto)
        headers = self._set_location_in_header(request, recipe.slug)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def _prepare_dto(self, request: Request) -> AddingTagsInputDto:
        serializer = serializers.TagsIdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        if request.method == 'POST':
            return AddingTagsInputDto(
                user=request.user,
                tag_ids=data['tag_ids']
            )
        else:
            return RemoveTagsInputDto(
                tag_ids=data['tag_ids']
            )


class RecipeIngredientsApi(BaseRecipeClass):
    """ API for retrieveing ingredients with unit and amount for given recipe"""

    def get(self, request, *args, **kwargs):
        recipe = self._get_object()
        data = selectors.recipe_get_ingredients(recipe)
        serializer = serializers.RecipeIngredientOutputSerializer(
            data, many=True)
        if serializer.data:
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        """ batch addition of ingredients with amount and unit to recipe """
        recipe = self._get_object()
        dto = self._prepare_recipe_ingredients_dto(recipe, request)
        service = AddIngredientsToRecipe()
        service.add(dto)
        headers = self._set_location_in_header(request, recipe.slug)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """ batch removal of ingredients from recipe """
        recipe = self._get_object()
        dto = self._prepare_dto(recipe, request)
        service = RemoveIngredientsFromRecipe()
        service.remove(dto)
        headers = self._set_location_in_header(request, recipe.slug)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def _prepare_dto(self, recipe: Recipe, request: Request) -> RecipeIngredientServiceDto:
        serializer = serializers.RecipeIngredientsInputSerializer(
            data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return RecipeIngredientServiceDto(
            user=request.user,
            recipe=recipe,
            ingredients=data
        )


class RecipeIngredientDetailApi(BaseRecipeClass):
    """ API for updating recipe ingredients """

    def put(self, request, *args, **kwargs):
        ingredient_id = kwargs.get('pk')
        recipe = self._get_object()
        recipe_ingredient = selectors.recipe_get_ingredient_details(
            recipe, ingredient_id)
        dto = self._prepare_dto(recipe_ingredient, request)
        service = UpdateRecipeIngredient()
        service.update(dto)
        headers = self._set_location_in_header(request, recipe.slug)
        return Response(headers=headers, status=status.HTTP_200_OK)

    def _prepare_dto(self, recipe_ingredient: Recipe_Ingredient, request: Request) -> UpdateRecipeIngredientDto:
        serializer = serializers.RecipeIngredientUpdateSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return UpdateRecipeIngredientDto(
            recipe_ingredient=recipe_ingredient,
            unit_id=data['unit'],
            amount=data['amount']
        )


class GroupRecipeDetailApi(BaseRecipeClass):
    """ API for retrieving recipes created by other users in joined groups """

    def get(self, request, *args, **kwargs):
        """ retrieve specific recipe based on slug """
        slug = kwargs.get('slug')
        recipe_creator_id = kwargs.get('pk')
        selectors.recipe_check_if_user_can_retrieve(
            requested_user=request.user, recipe_creator_id=recipe_creator_id)
        recipe_creator = users_selectors.user_get_by_id(recipe_creator_id)
        recipe = selectors.recipe_get(user=recipe_creator, slug=slug)
        serializer = serializers.GroupRecipeDetailOutpuSerializer(recipe)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class GroupRecipeTagsApi(BaseRecipeClass):
    """ API for retrieving group recipes tags """

    def get(self, request, *args, **kwargs):
        """ retrieve group recipe tags based on recipe slug """
        slug = kwargs.get('slug')
        recipe_creator_id = kwargs.get('pk')
        selectors.recipe_check_if_user_can_retrieve(
            requested_user=request.user, recipe_creator_id=recipe_creator_id)
        recipe_creator = users_selectors.user_get_by_id(recipe_creator_id)
        tags = selectors.tag_list_by_user_and_recipe(recipe_creator, slug)
        serializer = serializers.TagOutputSerializer(tags, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class GroupRecipeIngredientsApi(BaseRecipeClass):
    """ API for retrieving group recipes ingredients """

    def get(self, request, *args, **kwargs):
        """ retrieve group recipe ingredients based on recipe slug """
        slug = kwargs.get('slug')
        recipe_creator_id = kwargs.get('pk')
        selectors.recipe_check_if_user_can_retrieve(
            requested_user=request.user, recipe_creator_id=recipe_creator_id)
        recipe_creator = users_selectors.user_get_by_id(recipe_creator_id)
        recipe = selectors.recipe_get(recipe_creator, slug)
        ingredients = selectors.recipe_get_ingredients(recipe)
        serializer = serializers.RecipeIngredientOutputSerializer(
            ingredients, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class RecipeSendIngredientsToNozbe(BaseRecipeClass):
    """ API for sending recipes ingredients to nozbe """

    def post(self, request, *args, **kwargs):
        """ send ingredients to nozbe """
        if request.data:
            if selectors.ingredient_send_to_nozbe(request.data):
                return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
