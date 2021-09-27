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


class RecipeListOutputSerializer(serializers.ModelSerializer):
    """ serializing list of recipe objects """

    url = serializers.HyperlinkedIdentityField(view_name='recipe:recipe-detail',
                                               lookup_field='slug')
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = Recipe
        fields = (
            'url',
            'user',
            'name',
            'slug',
            'calories',
            'tags'
        )

    def to_representation(self, instance):
        """ update url field for recipes created by other user to avoid
         multi objects retrieving in detail view """
        ret = super().to_representation(instance)
        if ret['user'] != self.user.id:
            ret['url'] = reverse("recipe:recipe-detail", kwargs={
                                 'slug': ret['slug']},
                                 request=self.context['request']) + f"?user={ret['user']}"
        return ret

    def __init__(self, *args, **kwargs):
        """ set user """
        super().__init__(*args, **kwargs)
        try:
            self.user = self.context['user']
        except KeyError:
            self.user = self.context['request'].user


class RecipeDetailOutputSerializer(serializers.ModelSerializer):
    """ serializing recipe object """

    tags = CustomTagField(many=True, read_only=True)
    ingredients = CustomIngredientField(source='get_ingredients',
                                        many=True, read_only=True, )

    class Meta:
        model = Recipe
        fields = '__all__'

    def to_representation(self, instance):
        """ apend urls for tags and ingredients """
        ret = super().to_representation(instance)
        for tag in ret['tags']:
            tag.update({'url': reverse('recipe:tag-detail',
                                       request=self.context['request'],
                                       kwargs={'slug': tag['slug']})})
        for ingredient in ret['ingredients']:
            ingredient.update({'url': reverse('recipe:ingredient-detail',
                                              request=self.context['request'],
                                              kwargs={'slug': ingredient['slug']})})
        return ret


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

# class DynamicFieldsModelSerializer(serializers.ModelSerializer):
#
#     def __init__(self, *args, **kwargs):
#         fields = kwargs.pop('fields', None)
#         super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)
#
#         if fields is not None:
#             allowed = set(fields)
#             existing = set(self.fields)
#
#             for field_name in existing - allowed:
#                 self.fields.pop(field_name)
#
#
#
# class RecipeOutputSerializer(DynamicFieldsModelSerializer):
#     """ serialzier for outcomming Recipe objects """
#
#     url = serializers.HyperlinkedIdentityField(view_name='recipe:recipe-detail',
#                                                lookup_field='slug')
#
#     class Meta:
#         model = Recipe
#         fields = '__all__'
#
#     def to_representation(self, instance):
#         """ update url field for recipes created by other user to avoid multi objects retrieving in detail view """
#         ret = super().to_representation(instance)
#         if ret['user'] != self.user.id:
#             ret['url'] = reverse("recipe:recipe-detail", kwargs={
#                                     'slug': ret['slug']}, request=self.context['request']) + f"?user={ret['user']}"
#         return ret


# class RecipeOutputSerializer2(serializers.ModelSerializer):
#     """ serializing Recipe objects for retrieving """
#
#     url = serializers.HyperlinkedIdentityField(view_name='recipe:recipe-detail',
#                                                lookup_field='slug')
#     #tags = serializers.StringRelatedField(many=True)
#     #ingredients = IngredientOutputSerializer(many=True)
#
#     class Meta:
#         model = Recipe
#         exclude = ('photo1', 'photo2', 'photo3', 'description')
#
#     def to_representation(self, instance):
#         """ update url field for recipes created by other user to avoid multi objects retrieving in detail view """
#         ret = super().to_representation(instance)
#         if ret['user'] != self.user.id:
#             ret['url'] = reverse("recipe:recipe-detail", kwargs={
#                                     'slug': ret['slug']}, request=self.context['request']) + f"?user={ret['user']}"
#         return ret
#
#     def __init__(self, *args, **kwargs):
#         """ get user from context request when serialzier is init via view or get user
#         from context when serializer is init in tests """
#         super().__init__(*args, **kwargs)
#         try:
#             self.user = self.context['user']
#         except KeyError:
#             self.user = self.context['request'].user


# class IngredientSerializer(serializers.ModelSerializer):
#     """ Serializer for ingredient objects """
#
#     tags = TagSlugRelatedField(
#         many=True,
#         slug_field='name',
#         required=False,
#         write_only=True,
#     )
#     url = serializers.HyperlinkedIdentityField(view_name='recipe:ingredient-detail',
#                                                lookup_field='slug')
#     tag_information = TagSerializer(many=True, source="tags", read_only=True)
#
#     units = IngredientUnitSerializer(
#         many=True, write_only=True, required=False)
#     available_units = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Ingredient
#         exclude = ('id', )
#         read_only_fields = ('user', 'slug')
#
    # def to_representation(self, instance):
    #
    #     ret = super().to_representation(instance)
    #     try:
    #         user = self.context['user'].id
    #     except KeyError:
    #         user = None
    #     if user:
    #         if ret['user'] != self.context['user'].id:
    #             ret['url'] = reverse('recipe:ingredient-detail',
    #                                  kwargs={'slug': ret['slug']},
    #                                  request=self.context['request']) + f"?user={ret['user']}"
    #     return ret
#
#     def get_available_units(self, obj):
#         """ get defined unit for ingredient instance """
#         units = Ingredient_Unit.objects.filter(ingredient=obj)
#         return IngredientUnitSerializer(units, many=True, context={'request':
#                                                                    self.context['request']}).data
#
#     def validate_name(self, value):
#         """ check if ingredient with provided name is not already in db """
#         user = self.context['request'].user
#
#         queryset = Ingredient.objects.filter(user=user).filter(name=value)
#         check_if_name_is_in_db(self.instance, queryset)
#
#         return value
#
#     def update(self, instance, validated_data):
#         """ update instance with new unit mapping """
#         units = validated_data.pop('units', None)
#         ingredient = super().update(instance, validated_data)
#
#         if getattr(self.root, 'partial', False) is False:
#             instance.units.clear()
#         if units:
#             for unit in units:
#                 Ingredient_Unit.objects.update_or_create(
#                     ingredient=ingredient,
#                     unit=unit['unit'],
#                     defaults={'grams_in_one_unit': unit['grams_in_one_unit']}
#                 )
#         return instance


# class ReadyMealIngredientSerializer(IngredientSerializer):
#     """ serialzier for ready meals """
#
#     class Meta:
#         model = ReadyMeals
#         exclude = ('id', )
#         read_only_fields = ('user', 'slug')
#
#     def create(self, validated_data):
#         """ add default tag for ready meals """
#
#         user = self.context['request'].user
#         ready_meal_tag, created = Tag.objects.get_or_create(name='Ready Meal',
#                                                             user=user)
#         validated_data.update({"tags": [ready_meal_tag.id, ]})
#
#         return super().create(validated_data)

#
# class RecipeImageInputSerializer(serializers.Serializer):
#     """ Serializer for uploading images to recipes """
#
#     photo1 = serializers.ImageField(
#         required=False, use_url=False, allow_null=True)
#     photo2 = serializers.ImageField(
#         required=False, use_url=False, allow_null=True)
#     photo3 = serializers.ImageField(
#         required=False, use_url=False, allow_null=True)
