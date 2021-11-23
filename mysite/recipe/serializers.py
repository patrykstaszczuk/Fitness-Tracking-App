from rest_framework import serializers
from recipe.models import Ingredient, Tag, Recipe, Recipe_Ingredient, Unit, \
    Ingredient_Unit, ReadyMeals
from rest_framework import fields
from rest_framework.reverse import reverse
from django.core.exceptions import FieldError
from recipe.fields import CustomTagField, CustomIngredientField


def create_serializer_class(name, fields):
    return type(name, (serializers.Serializer, ), fields)


def inline_serializer(*, fields, data=None, **kwargs):
    serializer_class = create_serializer_class(name='', fields=fields)
    if data is not None:
        return serializer_class(data=data, **kwargs)

    return serializer_class(**kwargs)


class RecipeInputSerializer(serializers.Serializer):

    name = serializers.CharField()
    portions = serializers.IntegerField()
    prepare_time = serializers.IntegerField()
    description = serializers.CharField()


class RecipeListOutputSerializer(serializers.ModelSerializer):
    """ serializing list of recipe objects """

    # url = serializers.HyperlinkedIdentityField(view_name='recipe:recipe-detail',
    #                                            lookup_field='slug')
    # # tags = serializers.StringRelatedField(many=True)
    # tags = serializers.SerializerMethodField()
    _links = serializers.SerializerMethodField(method_name='get_links')

    class Meta:
        model = Recipe
        fields = (
            # 'url',
            'user',
            'name',
            'slug',
            'calories',
            '_links'
            # 'tags'
        )

    def get_links(self, instance) -> dict:
        """ prepare links to proepr endpoints """
        links = []
        links.append({
            'rel': 'self',
            'href': reverse('recipe:recipe-detail', kwargs={'slug': instance.slug}, request=self.context['request']),
            'actions': ['GET', 'PUT', 'DELETE']
        })
        links.append({
            'rel': 'tags',
            'href': reverse('recipe:recipe-tags',  kwargs={'slug': instance.slug}, request=self.context['request']),
            'actions': ['GET']
        })
        return links

    # def to_representation(self, instance):
    #     """ update url field for recipes created by other user to avoid
    #      multi objects retrieving in detail view """
    #     ret = super().to_representation(instance)
    #     if ret['user'] != self.user.id:
    #         ret['url'] = reverse("recipe:group-recipe-detail", kwargs={
    #                              'pk': ret['user'],
    #                              'slug': ret['slug']},
    #                              request=self.context['request'])
    #     return ret

    def __init__(self, *args, **kwargs):
        """ set user """
        super().__init__(*args, **kwargs)
        try:
            self.user = self.context['user']
        except KeyError:
            self.user = self.context['request'].user


class RecipeDetailOutputSerializer(serializers.ModelSerializer):
    """ serializing recipe object """

    _links = serializers.SerializerMethodField(method_name='get_links')

    class Meta:
        model = Recipe
        exclude = ('tags', 'ingredients')

    def get_links(self, instance) -> dict:
        """ prepare links to proepr endpoints """
        links = []
        self_rel = {
            'rel': 'self',
            'href': reverse('recipe:recipe-detail', kwargs={'slug': instance.slug}, request=self.context['request']),
            'actions': ['GET', 'PUT', 'DELETE']}

        links.append(self_rel)

        tags = {
            'rel': 'tags',
            'href': reverse('recipe:recipe-tags',  kwargs={'slug': instance.slug}, request=self.context['request']),
            'actions': ['GET']
        }
        links.append(tags)

        ingredients = {
            'rel': 'ingredients',
            'href': reverse('recipe:recipe-ingredients',  kwargs={'slug': instance.slug}, request=self.context['request']),
            'actions': ['GET']
        }
        links.append(ingredients)
        return links


class RecipeIngredientOutputSerializer(serializers.ModelSerializer):
    """ serializer for Recipe Ingredient intermediate model """

    ingredient = serializers.StringRelatedField()
    unit = serializers.StringRelatedField()

    class Meta:
        model = Recipe_Ingredient
        fields = ('ingredient', 'unit', 'amount')


class RecipeCreateInputSerializer(serializers.Serializer):
    """ serializing data for creating Recipe instance """

    name = serializers.CharField(required=True)
    tags = serializers.ListField(
        child=serializers.SlugField(), required=True)
    ingredients = inline_serializer(many=True, required=False, fields={
        'ingredient': serializers.SlugField(required=True),
        'amount': serializers.IntegerField(required=True),
        'unit': serializers.IntegerField(required=True)
    })
    portions = serializers.IntegerField(required=True)
    prepare_time = serializers.IntegerField(required=False)
    description = serializers.CharField(required=False)


class RecipePatchInputSerializer(RecipeCreateInputSerializer):
    """ set name and tags as not required during update """
    name = serializers.CharField(required=False)
    tags = serializers.ListField(
        child=serializers.SlugField(), required=False)
    portions = serializers.IntegerField(required=False)


class TagOutputSerializer(serializers.ModelSerializer):
    """ serializing Tag output data """

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'name')


class TagInputSerializer(serializers.Serializer):
    """ serializing Tag input data """
    name = serializers.CharField(max_length=25)


class IngredientListOutputSerializer(serializers.ModelSerializer):
    """ serializing ingredients instances """

    url = serializers.HyperlinkedIdentityField(view_name='recipe:ingredient-detail',
                                               lookup_field='slug')
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = Ingredient
        fields = ('url', 'name', 'slug', 'user', 'tags')


class IngredientUnitSerializer(serializers.ModelSerializer):
    """ read only serializer for serializing intermediate model for ingredient-unit """

    id = serializers.ReadOnlyField(source='unit.id')
    name = serializers.StringRelatedField(source='unit.name')

    class Meta:
        model = Ingredient_Unit
        fields = ('id', 'name', 'grams_in_one_unit')
        read_only_fields = ['unit', 'grams_in_one_unit']


class IngredientDetailOutputSerializer(serializers.ModelSerializer):
    """ serializing ingredient object """

    units = IngredientUnitSerializer(
        source='ingredient_unit_set', many=True, read_only=True)
    tags = CustomTagField(many=True, read_only=True)

    class Meta:
        model = Ingredient
        fields = '__all__'

    def to_representation(self, instance):
        """ set appropriate url based on user """
        ret = super().to_representation(instance)
        try:
            user = self.context['user'].id
        except KeyError:
            user = None
        if user:
            if ret['user'] != self.context['user'].id:
                ret['url'] = reverse('recipe:ingredient-detail',
                                     kwargs={'slug': ret['slug']},
                                     request=self.context['request']) + f"?user={ret['user']}"
        return ret


class IngredientInputSerializer(serializers.Serializer):
    """ serializing Ingredient input data """

    ready_meal = serializers.BooleanField(required=False)
    name = serializers.CharField(max_length=255, required=True)
    calories = serializers.FloatField(min_value=0, required=False)
    proteins = serializers.FloatField(min_value=0, required=False)
    carbohydrates = serializers.FloatField(min_value=0, required=False)
    fats = serializers.FloatField(min_value=0, required=False)
    tags = serializers.ListField(child=serializers.SlugField(), required=False)

    choices = [
        ('S', 'solid'),
        ('L', 'liquid')
    ]

    type = serializers.ChoiceField(choices, required=False)
    units = inline_serializer(many=True, required=False, fields={
        'unit': serializers.IntegerField(required=True),
        'grams_in_one_unit': serializers.IntegerField(required=True)
    })
    fiber = serializers.FloatField(min_value=0, required=False)
    sodium = serializers.FloatField(min_value=0, required=False)
    potassium = serializers.FloatField(min_value=0, required=False)
    calcium = serializers.FloatField(min_value=0, required=False)
    iron = serializers.FloatField(min_value=0, required=False)
    magnesium = serializers.FloatField(min_value=0, required=False)
    selenium = serializers.FloatField(min_value=0, required=False)
    zinc = serializers.FloatField(min_value=0, required=False)


class IngredientUpdateSerializer(IngredientInputSerializer):
    """ set name as non required since its update """

    name = serializers.CharField(max_length=255, required=False)


class UnitOutputSerializer(serializers.ModelSerializer):
    """ serializing available units """

    class Meta:
        model = Unit
        fields = '__all__'
