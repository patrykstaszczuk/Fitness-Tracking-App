from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from recipe.models import Ingredient, Tag
from recipe import serializers


class BaseRecipeAttrViewSet(viewsets.GenericViewSet,
                            mixins.ListModelMixin,
                            mixins.CreateModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.DestroyModelMixin):
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
