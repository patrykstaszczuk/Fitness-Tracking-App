from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import permissions

from mysite.renderers import CustomRenderer
from mysite.views import BaseAuthPermClass
from mysite.exceptions import ApiErrorsMixin

from recipe import selectors, services, serializers
from recipe.models import Recipe

from users import selectors as users_selectors

# class CanRetrieveRecipeDetail(BasePermission):
#     """ check if user has permission for retreiveing other user recipe detail """
#
#     def has_object_permission(self, request, view, obj):
#         """ check whether user is obj creator or is in obj creator group """
#         if request.user == obj.user:
#             return True
#         else:
#             if request.user in obj.user.own_group.members.all():
#                 return True
#         return False
#
#
# class IngredientListApi(BaseAuthPermClass, RequiredFieldsResponseMessage):
#     """ API for handlig ingredients list """
#
#     def get(self, request, *args, **kwargs):
#         """ handling get request """
#         user_ingredients = selectors.ingredient_list(user=request.user)
#
#         fields = ('user', 'name', 'slug', 'url', 'type',
#                   'proteins', 'carbohydrates', 'fats', 'tags')
#         serializer = serializers.IngredientOutputSerializer(
#             user_ingredients, fields=fields, many=True,
#             context=self.get_serializer_context())
#         return Response(data=serializer.data, status=status.HTTP_200_OK)
#
#
# class IngredientDetailApi(BaseAuthPermClass, RequiredFieldsResponseMessage):
#     """ API for handling ingredient detail """
#
#     def get(self, request, *args, **kwargs):
#         """ handling get request """
#         slug = kwargs.get('slug')
#         ingredient = selectors.ingredient_get(slug)
#         serializer = serializers.IngredientOutputSerializer(
#             ingredient, context=self.get_serializer_context())
#
#         available_units = selectors.ingredient_get_available_units(
#             ingredient)
#         available_units_dict = serializers.IngredientUnitOutputSerializer(
#             available_units, many=True).data
#         response_data = serializer.data
#         response_data.update({'available_units': available_units_dict})
#         return Response(data=response_data, status=status.HTTP_200_OK)
#
#     def delete(self, request, *args, **kwargs):
#         """ handling delete request """
#         slug = kwargs.get('slug')
#         ingredient = selectors.ingredient_get_for_requested_user(
#             user=request.user, slug=slug)
#         ingredient.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
#
#
# class IngredientCreateApi(BaseAuthPermClass, RequiredFieldsResponseMessage):
#     """ API for creating ingredients """
#
#     def post(self, request, *args, **kwargs):
#         """ handling post request """
#         serializer = serializers.IngredientInputSerializer(data=request.data)
#         if serializer.is_valid():
#             ingredient = services.ingredient_create(
#                 user=request.user, data=serializer.data)
#             serializer = serializers.IngredientOutputSerializer(
#                 ingredient, context=self.get_serializer_context())
#             return Response(data=serializer.data, status=status.HTTP_201_CREATED)
#         return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class IngredientUpdateApi(BaseAuthPermClass, RequiredFieldsResponseMessage):
#     """ API for updating ingredients """
#
#     def put(self, request, *args, **kwargs):
#         """ handling update request """
#         slug = kwargs.get('slug')
#         ingredient = selectors.ingredient_get_for_requested_user(
#             user=request.user, slug=slug)
#         serializer = serializers.IngredientInputSerializer(data=request.data)
#         if serializer.is_valid():
#             ingredient = services.ingredient_update(
#                 ingredient, data=serializer.data, method=request.method)
#             serializer = serializers.IngredientOutputSerializer(
#                 ingredient, context=self.get_serializer_context())
#
#             available_units = selectors.ingredient_get_available_units(
#                 ingredient)
#             available_units_dict = serializers.IngredientUnitOutputSerializer(
#                 available_units, many=True).data
#
#             response_data = serializer.data
#             response_data.update({'available_units': available_units_dict})
#             return Response(data=response_data, status=status.HTTP_200_OK)
#         return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def patch(self, request, *args, **kwargs):
#         """ return put method, but remove m2m fields """
#         return self.put(request, *args, **kwargs)
#
#
# class UnitViewSet(BaseAuthPermClass, RequiredFieldsResponseMessage):
#     """ viewset for retrieving available units """
#
#     def get(self, request, *args, **kwargs):
#         """ return all avilable units """
#         units = selectors.unit_list()
#         if units.count() > 0:
#             serializer = serializers.UnitOutputSerializer(units, many=True)
#             return Response(data=serializer.data, status=status.HTTP_200_OK)
#         return Response(status=status.HTTP_204_NO_CONTENT)
#
#


class BaseViewClass(BaseAuthPermClass, ApiErrorsMixin, APIView):
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]

    def get_serializer_context(self):
        """ Extra context provided to the serializer class. """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }


class RecipeBaseViewClass(BaseViewClass):
    """ base class for Recipe API """

    def set_location_in_header(self, recipe_slug: str, request: Request) -> dict:
        """ set location with proper url in header """
        return {'Location': reverse(
            'recipe:recipe-detail', request=request,
                kwargs={'slug': recipe_slug})}


class RecipeListApi(RecipeBaseViewClass):
    """ API for listing recipes """

    def get(self, request, *args, **kwargs):
        """ retrive all available recipe for user """
        recipes = selectors.recipe_list(
            user=request.user, filters=request.query_params)
        serializer = serializers.RecipeListOutputSerializer(
            recipes, many=True, context=self.get_serializer_context())
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class RecipeDetilApi(RecipeBaseViewClass):
    """ API for retreving specific recipe """

    def get(self, request, *args, **kwargs):
        """ retrive specific recipe based on slug """
        slug = kwargs.get('slug')
        recipe = selectors.recipe_get(user=request.user, slug=slug)
        serializer = serializers.RecipeDetailOutputSerializer(recipe)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class GroupRecipeDetailApi(RecipeBaseViewClass):
    """ API for retrieving recipes created by other users in joined groups """

    def get(self, request, *args, **kwargs):
        """ retrieve specific recipe based on slug """
        slug = kwargs.get('slug')
        recipe_creator_id = kwargs.get('pk')

        selectors.recipe_check_if_user_can_retrieve(
            requested_user=request.user, recipe_creator_id=recipe_creator_id)
        recipe_creator = users_selectors.user_get_by_id(recipe_creator_id)
        recipe = selectors.recipe_get(user=recipe_creator, slug=slug)

        serializer = serializers.RecipeDetailOutputSerializer(recipe)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class RecipeCreateApi(RecipeBaseViewClass):
    """ API for creating recipes """

    def post(self, request, *args, **kwargs):
        """ handling creation process and return response """
        serializer = serializers.RecipeCreateInputSerializer(data=request.data)
        if serializer.is_valid():
            recipe_service = services.RecipeService(
                user=request.user, data=serializer.data)
            recipe = recipe_service.create()
            headers = self.set_location_in_header(recipe.slug, request)
            return Response(status=status.HTTP_201_CREATED, headers=headers)
        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class BaseTagViewClass(BaseViewClass):
    """ base class for tag APIs """

    def set_location_in_header(self, tag_slug: str, request: Request) -> dict:
        """ set location with proper url in header """
        return {'Location': reverse(
            'recipe:tag-detail', request=request, kwargs={'slug': tag_slug})}


class TagListApi(BaseTagViewClass):
    """ API for listing tags """

    def get(self, request, *args, **kwargs):
        """ handling get request """
        user_tags = selectors.tag_list(user=request.user)
        serializer = serializers.TagOutputSerializer(user_tags, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class TagDetailApi(BaseTagViewClass):
    """ API for listing tags """

    def get(self, request, *args, **kwargs):
        """ handling get request """
        slug = kwargs.get('slug')
        user_tag = selectors.tag_get(user=request.user, slug=slug)
        serializer = serializers.TagOutputSerializer(user_tag)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class TagCreateApi(BaseTagViewClass):
    """ API for creating tags """

    def post(self, request, *args, **kwargs):
        """ handling post request """
        serializer = serializers.TagInputSerializer(data=request.data)
        if serializer.is_valid():
            tag_service = services.TagService(
                user=request.user, data=serializer.data)
            tag = tag_service.create()
            headers = self.set_location_in_header(tag.slug, request=request)
            return Response(status=status.HTTP_201_CREATED, headers=headers)
        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class TagUpdateApi(BaseTagViewClass):
    """ API for updating and deleteing tag """

    def put(self, request, *args, **kwargs):
        """ handling put action """
        slug = kwargs.get('slug')
        tag = selectors.tag_get(request.user, slug)
        serializer = serializers.TagInputSerializer(data=request.data)
        if serializer.is_valid():
            tag_service = services.TagService(request.user, serializer.data)
            tag = tag_service.update(instance=tag)
            headers = self.set_location_in_header(tag.slug, request)
            return Response(status=status.HTTP_200_OK)
        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class TagDeleteApi(BaseTagViewClass):
    """ API for deleteing tags """

    def delete(self, request, *args, **kwargs):
        """ retrieve and delete tag """
        slug = kwargs.get('slug')
        tag = selectors.tag_get(request.user, slug)
        tag.delete()
        return Response(data=None, status=status.HTTP_200_OK)


class IngredientBaseViewClass(BaseViewClass):
    """ base class for ingredients APIs """

    def set_location_in_header(self, ingredient_slug: str, request: Request) -> dict:
        """ set location with proper url in header """
        return {'Location': reverse(
            'recipe:ingredient-detail', request=request, kwargs={'slug': ingredient_slug})}


class IngredientListApi(IngredientBaseViewClass):
    """ API for handlig ingredients list """

    def get(self, request, *args, **kwargs):
        """ handling get request """
        user_ingredients = selectors.ingredient_list(user=request.user)
        serializer = serializers.IngredientListOutputSerializer(
            user_ingredients, many=True, context=self.get_serializer_context())
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class IngredientDetailApi(IngredientBaseViewClass):
    """ API for handling ingredient detail """

    def get(self, request, *args, **kwargs):
        """ handling get request """
        slug = kwargs.get('slug')
        ingredient = selectors.ingredient_get(slug)
        serializer = serializers.IngredientDetailOutputSerializer(
            ingredient)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class IngredientCreateApi(IngredientBaseViewClass):
    """ API for creating ingredients """

    def post(self, request, *args, **kwargs):
        """ handling post request """
        serializer = serializers.IngredientInputSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            ingredient_service = services.IngredientService(
                user=request.user, data=data)
            ingredient = ingredient_service.create()
            headers = self.set_location_in_header(ingredient.slug, request)
            return Response(status=status.HTTP_201_CREATED, headers=headers)
        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class IngredientUpdateApi(IngredientBaseViewClass):
    """ API for updating ingredients """

    def put(self, request, *args, **kwargs):
        """ handling update request """
        request = self.request
        slug = kwargs.get('slug')
        partial = kwargs.get('partial', False)
        ingredient = selectors.ingredient_get_only_for_user(request.user, slug)
        serializer = serializers.IngredientUpdateSerializer(data=request.data)
        if serializer.is_valid():
            ingredient_service = services.IngredientService(
                user=request.user, data=serializer.data)
            ingredient = ingredient_service.update(ingredient, partial=partial)
            headers = self.set_location_in_header(ingredient.slug, request)
            return Response(status=status.HTTP_200_OK, headers=headers)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        """ handle update like patch but set partial as true """
        kwargs.update({'partial': True})
        return self.put(self, request, *args, **kwargs)


class IngredientDeleteApi(IngredientBaseViewClass):
    """ API for delete ingredients """

    def delete(self, request, *args, **kwargs):
        """ handling delete request """
        slug = kwargs.get('slug')
        ingredient = selectors.ingredient_get_only_for_user(request.user, slug)
        services.IngredientService.delete(ingredient)
        return Response(status=status.HTTP_200_OK)
