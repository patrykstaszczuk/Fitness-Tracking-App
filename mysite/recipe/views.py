from rest_framework.decorators import action
from rest_framework.reverse import reverse
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, BasePermission
from recipe.models import Ingredient, Tag, Recipe, Unit
from users.models import Group
from recipe import serializers
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import permissions

from mysite.renderers import CustomRenderer
from mysite.views import RequiredFieldsResponseMessage

from recipe import selectors, services


class CanRetrieveRecipeDetail(BasePermission):
    """ check if user has permission for retreiveing other user recipe detail """

    def has_object_permission(self, request, view, obj):
        """ check whether user is obj creator or is in obj creator group """
        if request.user == obj.user:
            return True
        else:
            if request.user in obj.user.own_group.members.all():
                return True
        return False


class BaseRecipeAttrViewSet(RequiredFieldsResponseMessage, viewsets.ModelViewSet):
    """ Base viewset for user owned recipe atributes """
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]
    lookup_field = "slug"

    def get_queryset(self, extra_action=False):
        """ return objects for the current authenticated user only """

        if extra_action:
            user_in_url = self.request.query_params.get('user', None)
            if user_in_url and self.action == 'retrieve':
                return self.queryset.filter(user=user_in_url)
            elif user_in_url and self.action not in permissions.SAFE_METHODS:
                return self.http_method_not_allowed(self.request)
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """ create a new object """
        serializer.save(user=self.request.user)

    def perfom_update(self, serializer):
        """ update an existing object """
        serializer.save(user=self.request.user)

    def get_serializer_context(self):
        """ set user to context """
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context


class IngredientViewSet(BaseRecipeAttrViewSet):
    """ Manage ingredient in the database """
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()

    def get_queryset(self):
        """
        list -> all ingredients in db
        retrieve -> depends on user in query query
        non-safe methods -> only requrested user objects
        """
        if self.action in ['list', ]:
            return self.queryset
        else:
            return super().get_queryset(extra_action=True)

    def get_serializer_class(self):
        """ return different serializer if ready_meal flag is True """

        flag = self.request.data.get('ready_meal')
        if flag is True:
            return serializers.ReadyMealIngredientSerializer
        return self.serializer_class


class TagViewSet(RequiredFieldsResponseMessage, viewsets.ModelViewSet):
    """ Manage tag in the database """
    # serializer_class = serializers.TagSerializer
    # queryset = Tag.objects.all()
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]
    lookup_field = "slug"

    def get_queryset(self):
        """ return tags only for authenticated user """
        return selectors.tags_get(user=self.request.user)

    def get(self, request, *args, **kwargs):
        """ retrieve all tags created by user """
        print("Dasda")


class RecipeViewSet(RequiredFieldsResponseMessage, viewsets.ModelViewSet):
    """ endpoint for handling recipes """
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, CanRetrieveRecipeDetail)
    renderer_classes = [CustomRenderer, ]
    lookup_field = 'slug'

    def get_queryset(self, extra_action=False):
        """ return recipes for requested user or other user in group """

        user_in_url = self.request.query_params.get('user', None)
        if user_in_url and self.action == 'retrieve':
            return selectors.get_recipes(user=self.request.user, url_user=user_in_url)
        elif user_in_url and self.action not in permissions.SAFE_METHODS:
            return self.http_method_not_allowed(self.request)
        return selectors.get_recipes(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """ retreive recipe detail """
        instance = self.get_object()
        serializer = serializers.RecipeOutputSerializer(
            instance=instance, context=self.get_serializer_context())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        """ list all avilable recipes for requested user """

        filters = request.query_params
        available_recipes = selectors.get_recipes(
            user=request.user, filters=filters)
        serializer = serializers.RecipeOutputSerializer(
            available_recipes, many=True, context=self.get_serializer_context())
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """ create new recipe """

        serializer = serializers.RecipeInputSerializer(
            data=request.data, context=self.get_serializer_context())
        if serializer.is_valid():
            obj = services.create_recipe(
                user=request.user, data=serializer.data)
            serializer = serializers.RecipeOutputSerializer(
                obj, context=self.get_serializer_context())
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """ update recipe """
        recipe = self.get_object()
        serializer = serializers.RecipeInputSerializer(data=request.data)
        if serializer.is_valid():
            obj = services.update_recipe(recipe=recipe,
                                         data=serializer.data,
                                         method=self.request.method)
            serializer = serializers.RecipeOutputSerializer(
                obj, context=self.get_serializer_context())
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """ delete recipe """
        instance = self.get_object()
        services.delete_recipe(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_renderer_context(self):
        """ override for extra links """
        context = super().get_renderer_context()

        if self.action == 'retrieve':
            slug = self.kwargs.get('slug')
            links = {
                'recipes-list': reverse('recipe:recipe-list', request=self.request),
                'availabe-units': reverse('recipe:units', request=self.request),
                # 'send_to_nozbe': reverse('recipe:recipe-send-to-nozbe',
                #                          args=[slug], request=self.request),
                # 'upload_image': reverse('recipe:recipe-upload-image',
                #                         args=[slug], request=self.request),
            }
        else:
            links = {
                'availabe-units': reverse('recipe:units', request=self.request)
            }
        context['links'] = links
        return context

    @action(methods=['PUT'], detail=True, url_path='add-to-nozbe')
    def send_to_nozbe(self, request, slug=None):
        """ send provided ingredients to nozbe"""

        if request.data:
            if selectors.send_ingredients_to_nozbe(request.data):
                return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

#     @action(methods=['POST', 'GET'], detail=True, url_path='add-photos')
#     def upload_image(self, request, slug=None):
#         """ upload an image to a recipe """

#         recipe = self.get_object()
#         serializer = self.get_serializer(
#             recipe,
#             data=request.data
#         )

#         if serializer.is_valid():
#             serializer.save()
#             headers = {}
#             if request.method == 'POST':

#                 headers['Location'] = reverse('recipe:recipe-detail',
#                                               kwargs={'slug': slug},
#                                               request=request)
#             return Response(
#                 serializer.data,
#                 status=status.HTTP_200_OK,
#                 headers=headers
#             )
#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST
#         )


class UnitViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """ viewset for retrieving available units """

    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.UnitSerializer
    queryset = Unit.objects.all()
