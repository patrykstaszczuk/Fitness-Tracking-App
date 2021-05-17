from rest_framework.decorators import action
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from recipe.models import Ingredient, Tag, Recipe
from recipe import serializers
from django.db.models import Q
from recipe import models
from django.shortcuts import get_object_or_404


class BaseRecipeAttrViewSet(viewsets.ModelViewSet):
    """ Base viewset for user owned recipe atributes """
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    lookup_field = "slug"

    def get_queryset(self):
        """ return objects for the current authenticated user only """
        return self.queryset.filter(user=self.request.user). \
            order_by('-name')

    def perform_create(self, serializer):
        """ create a new object """
        serializer.save(user=self.request.user)

    def perfom_update(self, serializer):
        """ update an existing object """
        serializer.save(user=self.request.user)


class IngredientViewSet(BaseRecipeAttrViewSet):
    """ Manage ingredient in the database """
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


class TagViewSet(BaseRecipeAttrViewSet):
    """ Manage tag in the database """
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class RecipeViewSet(BaseRecipeAttrViewSet):
    """ Manage recipe in the database """
    serializer_class = serializers.RecipeSerializer
    queryset = Recipe.objects.all()
    lookup_field = 'slug'

    def _return_users_from_common_groups(self, user):
        """ return all users belongs to groups where requested user is
        member """

        users_instances = []

        request_user_groups = user.membership.all()
        users_instances_in_groups = [group.members.all() for group
                                     in request_user_groups]
        for group_members in users_instances_in_groups:
            for user in group_members:
                users_instances.append(user)
        return list(set(users_instances))

    def get_object(self):
        return Recipe.objects.get(slug=self.kwargs.get('slug'))

    def get_queryset(self):
        """ Retrieve the recipes for authenticated user with filtering if
        applied """

        users_in_groups = self._return_users_from_common_groups(self.request.user)

        filter_tags = self.request.query_params.get('tags')
        # filter_ingredients = self.request.query_params.get('ingredients')

        if filter_tags:
            filter_tags = filter_tags.split(',')
            return self.queryset.filter(Q(user=self.request.user) |
                                        Q(user__in=users_in_groups)). \
                filter(tags__slug__in=filter_tags).order_by('-name')


        # if filter_ingredients:
        #     filter_ingredients = filter_ingredients.split(',')
        #     return self.queryset.filter(user=self.request.user). \
        #         filter(ingredients__slug__in=filter_ingredients) \
        #         .order_by('-name')

        return self.queryset.filter(Q(user=self.request.user) |
                                    Q(user__in=users_in_groups)).\
            order_by('-name')

    def get_serializer_class(self):
        """ return appropriate serializer class """
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def _validate_ingredients(self, ingredients):
        """ validate that passed ingredient slug's can be mapped to models
         object"""

        ingredient_queryset = Ingredient.objects.filter(slug__in=ingredients)
        if ingredient_queryset.count() == len(ingredients):
            return ingredient_queryset
        return Response(status.HTTP_400_BAD_REQUEST)

    @action(methods=['PUT'], detail=True, url_path='dodaj-do-nozbe')
    def send_to_nozbe(self, request, slug=None):

        ingredients = self._validate_ingredients(request.data)

        for ingredient in ingredients:
            ingredient.send_to_nozbe()
        serializer = serializers.IngredientSerializer(ingredients, many=True)
        return Response(serializer.data)

    @action(methods=['POST', 'GET'], detail=True, url_path='dodaj-zdjecie')
    def upload_image(self, request, slug=None):
        """ upload an image to a recipe """
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class RecipeDetailViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    """ Detail View for handling group recipes detail """

    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()

    def get_object(self):
        """ retrieve object based on pk and slug. Recipes in groups can have
        same name """
        user_id = self.kwargs.get('pk')
        slug = self.kwargs.get('slug')
        instance = get_object_or_404(Recipe, user=user_id, slug=slug)
        return instance
