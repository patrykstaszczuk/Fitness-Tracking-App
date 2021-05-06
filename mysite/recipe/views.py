from rest_framework.decorators import action
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from recipe.models import Ingredient, Tag, Recipe
from recipe import serializers

from django.db.models.signals import post_delete, pre_save
from django.dispatch.dispatcher import receiver


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

    def get_serializer_class(self):
        """ return appropriate serializer class """
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

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
