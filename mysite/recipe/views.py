from rest_framework.decorators import action
from rest_framework.reverse import reverse
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from recipe.models import Ingredient, Tag, Recipe, Unit
from users.models import Group
from recipe import serializers
from django.shortcuts import get_object_or_404
from django.http import Http404

from mysite.renderers import CustomRenderer
from mysite.views import RequiredFieldsResponseMessage


class BaseRecipeAttrViewSet(RequiredFieldsResponseMessage, viewsets.ModelViewSet):
    """ Base viewset for user owned recipe atributes """
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]
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

    def get_queryset(self):
        """ Retrieve the recipes for authenticated user with filtering if
        applied """
        return self._get_filtering(request=self.request)

    def get_serializer_class(self):
        """ return appropriate serializer class """
        detailedActions = ['retrieve', 'update', 'partial_update']
        if self.action in detailedActions:
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def get_renderer_context(self):
        """ override for extra links """
        context = super().get_renderer_context()

        if self.action == 'retrieve':
            slug = self.kwargs.get('slug')
            links = {
                'recipes-list': reverse('recipe:recipe-list', request=self.request),
                'availabe-units': reverse('recipe:units', request=self.request),
                'send_to_nozbe': reverse('recipe:recipe-send-to-nozbe',
                                         args=[slug], request=self.request),
                'upload_image': reverse('recipe:recipe-upload-image',
                                        args=[slug], request=self.request),
            }
        else:
            links = {
                'availabe-units': reverse('recipe:units', request=self.request)
            }
        context['links'] = links
        return context

    def _validate_ingredients(self, ingredients):
        """ validate that passed ingredient slug's can be mapped to models
         object"""

        ingredient_queryset = Ingredient.objects.filter(slug__in=ingredients)
        if ingredient_queryset.count() == len(ingredients):
            return ingredient_queryset
        return Response(status.HTTP_400_BAD_REQUEST)

    @action(methods=['PUT'], detail=True, url_path='add-to-nozbe')
    def send_to_nozbe(self, request, slug=None):
        """ send provided ingredients to nozbe """

        ingredients = self._validate_ingredients(request.data)

        for ingredient in ingredients:
            ingredient.send_to_nozbe()
        serializer = serializers.IngredientSerializer(ingredients, many=True,
                                                      context={'request': request})
        return Response(serializer.data)

    @action(methods=['POST', 'GET'], detail=True, url_path='add-photos')
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

    def _get_filtering(self, request):
        """ check if there is any filter applied and return queryset if so """

        allowed_filters = ['tags', 'groups']
        user = self.request.user
        filtered_groups = request.query_params.get('groups')
        allowed_filters.pop()

        users_in_filtered_groups = \
            self._return_users_from_filtered_groups(user, filtered_groups)
        queryset = Recipe.objects.all().filter(user__in=
                                               users_in_filtered_groups).order_by('-name')

        for filter in request.query_params:
            if filter in allowed_filters:
                filter_values = request.query_params[filter].split(',')
                filter_instances = self._map_raw_data_to_instances(Tag, user,
                                                                   'slug',
                                                                   filter_values)
                query = filter + '__in'
                queryset = queryset.filter(**{query: filter_instances})
        return queryset

    def _return_users_from_filtered_groups(self, user, groups):
        """ return all users belongs to filtered groups """

        users_instances = []

        if groups is not None:
            groups = groups.split(',')
            groups = self._map_raw_data_to_instances(Group, user, 'id', groups)
        else:
            groups = user.membership.all()

        users_instances_in_groups = [group.members.all() for group in groups]

        for group_members in users_instances_in_groups:
            for user in group_members:
                users_instances.append(user)
        return list(set(users_instances))

    def _map_raw_data_to_instances(self, instance, user, lookup_key, data):
        """ map provided filtering data to instances """

        instances_list = []
        for item in data:
            try:
                if instance == Group:
                    objs = user.membership.all()
                else:
                    objs = instance.objects.filter(user=user)
                obj = objs.get(**{lookup_key: item})
                instances_list.append(obj)
            except instance.DoesNotExist:
                pass
        return instances_list


class RecipeDetailViewSet(RequiredFieldsResponseMessage,
                          viewsets.GenericViewSet,
                          mixins.RetrieveModelMixin):
    """ Detail View for handling group recipes detail. Only GET is allowed,
    becouse user is not allowed to modify other users recipe. If user wants
    to modify his own recipe he must go to standard detail recipe url
    provided by router
    """

    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()

    def get_object(self):
        """ retrieve object based on pk and slug. Recipes in groups can have
        same name """
        user_id = self.kwargs.get('pk')
        slug = self.kwargs.get('slug')

        try:
            user_id = int(user_id)
        except ValueError:
            raise Http404('Identyfikator użytkownika musi być liczbą!')

        instance = get_object_or_404(Recipe, user=user_id, slug=slug)
        return instance


class UnitViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """ viewset for retrieving available units """

    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    serializer_class = serializers.UnitSerializer
    queryset = Unit.objects.all()
