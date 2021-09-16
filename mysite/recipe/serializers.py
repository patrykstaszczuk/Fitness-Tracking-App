from rest_framework import serializers
from recipe.models import Ingredient, Tag, Recipe, Recipe_Ingredient, Unit, \
    Ingredient_Unit, ReadyMeals
from rest_framework import fields
from rest_framework.reverse import reverse
from django.core.exceptions import FieldError


class DynamicFieldsModelSerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)

            for field_name in existing - allowed:
                self.fields.pop(field_name)


def create_serializer_class(name, fields):
    return type(name, (serializers.Serializer, ), fields)


def inline_serializer(*, fields, data=None, **kwargs):
    serializer_class = create_serializer_class(name='', fields=fields)
    if data is not None:
        return serializer_class(data=data, **kwargs)

    return serializer_class(**kwargs)


class IngredientOutputSerializer(serializers.ModelSerializer):
    """ serializing Ingredient instances """

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeOutputSerializer(serializers.ModelSerializer):
    """ serializing Recipe objects for retrieving """

    url = serializers.HyperlinkedIdentityField(view_name='recipe:recipe-detail',
                                               lookup_field='slug')
    tags = serializers.StringRelatedField(many=True)
    ingredients = IngredientOutputSerializer(many=True)

    class Meta:
        model = Recipe
        exclude = ('photo1', 'photo2', 'photo3', 'description')

    def to_representation(self, instance):
        """ update url field for recipes created by other user to avoid multi objects retrieving in detail view """
        ret = super().to_representation(instance)
        if ret['user'] != self.user.id:
            ret['url'] = reverse("recipe:recipe-detail", kwargs={
                                    'slug': ret['slug']}, request=self.context['request']) + f"?user={ret['user']}"
        return ret

    def __init__(self, *args, **kwargs):
        """ get user from context request when serialzier is init via view or get user
        from context when serializer is init in tests """
        super().__init__(*args, **kwargs)
        try:
            self.user = self.context['user']
        except KeyError:
            self.user = self.context['request'].user


class RecipeInputSerializer(serializers.Serializer):
    """ serializing data for creating Recipe instance """

    name = serializers.CharField(required=False)
    tags = serializers.ListField(child=serializers.SlugField(), required=False)
    ingredients = inline_serializer(many=True, required=False, fields={
        'ingredient': serializers.SlugField(required=True),
        'amount': serializers.IntegerField(required=True),
        'unit': serializers.IntegerField(required=True)
    })
    portions = serializers.IntegerField(required=False)
    prepare_time = serializers.IntegerField(required=False)
    description = serializers.CharField(required=False)


def raise_validation_error(instance):
    """" raise validation error for instance """
    raise serializers.ValidationError('Ta nazwa jest już zajęta !')


def check_if_name_is_in_db(instance, queryset):
    """ check if provided name is already used, if so call
    raise_validation_error function """
    if instance is None:
        if queryset.exists():
            raise_validation_error(instance)
    else:
        if queryset.exclude(id=instance.id):
            raise_validation_error(instance)


class UnitSerializer(serializers.ModelSerializer):
    """ serializer for Unit model """

    class Meta:
        model = Unit
        fields = '__all__'


class TagSlugRelatedField(serializers.SlugRelatedField):
    """ Filter all returned slug tags by specific user """

    def get_queryset(self):
        user = self.context['request'].user
        queryset = Tag.objects.filter(user=user)
        return queryset


class IngredientUnitSerializer(serializers.ModelSerializer):
    """ Serializer for Ingredient Unit intermediate model """

    unit_name = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient_Unit
        fields = '__all__'

    def get_unit_name(self, obj):
        """ get unit name for ingredient unit mapping information """
        return obj.unit.name


class TagSerializer(serializers.ModelSerializer):
    """ Serializer for tag objects """

    url = serializers.HyperlinkedIdentityField(view_name='recipe:tag-detail',
                                               lookup_field='slug')

    class Meta:
        model = Tag
        exclude = ('id',)
        read_only_fields = ('id', 'user', 'slug')

    def validate_name(self, value):
        """ check if tag with provided name is not already in db """

        user = self.context['request'].user
        queryset = Tag.objects.filter(user=user).filter(name=value)
        check_if_name_is_in_db(self.instance, queryset)

        return value


class IngredientSerializer(serializers.ModelSerializer):
    """ Serializer for ingredient objects """

    tags = TagSlugRelatedField(
        many=True,
        slug_field='name',
        required=False,
        write_only=True,
    )
    url = serializers.HyperlinkedIdentityField(view_name='recipe:ingredient-detail',
                                               lookup_field='slug')
    tag_information = TagSerializer(many=True, source="tags", read_only=True)

    units = IngredientUnitSerializer(
        many=True, write_only=True, required=False)
    available_units = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        exclude = ('id', )
        read_only_fields = ('user', 'slug')

    def to_representation(self, instance):

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

    def get_available_units(self, obj):
        """ get defined unit for ingredient instance """
        units = Ingredient_Unit.objects.filter(ingredient=obj)
        return IngredientUnitSerializer(units, many=True, context={'request':
                                                                   self.context['request']}).data

    def validate_name(self, value):
        """ check if ingredient with provided name is not already in db """
        user = self.context['request'].user

        queryset = Ingredient.objects.filter(user=user).filter(name=value)
        check_if_name_is_in_db(self.instance, queryset)

        return value

    def update(self, instance, validated_data):
        """ update instance with new unit mapping """
        units = validated_data.pop('units', None)
        ingredient = super().update(instance, validated_data)

        if getattr(self.root, 'partial', False) is False:
            instance.units.clear()
        if units:
            for unit in units:
                Ingredient_Unit.objects.update_or_create(
                    ingredient=ingredient,
                    unit=unit['unit'],
                    defaults={'grams_in_one_unit': unit['grams_in_one_unit']}
                )
        return instance


class ReadyMealIngredientSerializer(IngredientSerializer):
    """ serialzier for ready meals """

    class Meta:
        model = ReadyMeals
        exclude = ('id', )
        read_only_fields = ('user', 'slug')

    def create(self, validated_data):
        """ add default tag for ready meals """

        user = self.context['request'].user
        ready_meal_tag, created = Tag.objects.get_or_create(name='Ready Meal',
                                                            user=user)
        validated_data.update({"tags": [ready_meal_tag.id, ]})

        return super().create(validated_data)


# class IngredientSlugRelatedField(serializers.SlugRelatedField):
#     """ Filter all returned slug ingredients by specyfic user """
#
#     def get_queryset(self):
#         user = self.context['request'].user
#         queryset = Ingredient.objects.filter(user=user)
#         return queryset


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """ serializer for intermediate model for recipe and ingredient, with
        field quantity """

    ingredient = serializers.SlugRelatedField(
            queryset=Ingredient.objects.all(),
            slug_field='slug',
            required=True,
            write_only=True
    )
    ingredient_detail = IngredientSerializer(read_only=True,
                                             source='ingredient')

    class Meta:
        model = Recipe_Ingredient
        fields = ('ingredient', 'ingredient_detail', 'amount', 'unit')

    def validate(self, values):
        """ validate if all fields are provided in json request and unit
        validation """

        fields = self.fields
        fields.pop('ingredient_detail', None)
        for field in fields:
            if field not in values:
                raise serializers.ValidationError(f'{field} have to be set')
        ingredient = values.get('ingredient')

        unit = values.get('unit')
        available_units = ingredient.units.all()
        if unit not in available_units:
            available_units_names = []
            for unit in available_units:
                available_units_names.append(unit.name)
            raise serializers.ValidationError(f'{unit} is not defined for \
             {ingredient.name}. Available units: {available_units_names}')
        return values


class RecipeSerializer(serializers.ModelSerializer):
    """ serializer for recipe objects """

    url = serializers.HyperlinkedIdentityField(view_name='recipe:recipe-detail',
                                               lookup_field='slug')
    tags = TagSlugRelatedField(
        many=True,
        slug_field='slug',
        required=True,
        write_only=True
    )
    tag_detail = TagSerializer(Tag.objects.all(), many=True, source='tags',
                               read_only=True)
    ingredients = RecipeIngredientSerializer(
                                             required=False,
                                             many=True,
                                             write_only=True,
                                             source='ingredients_quantity',
                                             )

    class Meta:
        model = Recipe
        exclude = ('proteins', 'carbohydrates', 'fats')
        read_only_fields = ('url', 'user', 'slug', 'photo1', 'photo2',
                            'photo3', 'calories')
        extra_kwargs = {
            'portions': {'write_only': True},
            'prepare_time': {'write_only': True},
            'description': {'write_only': True}
        }

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = super().to_representation(instance)
        if ret['user'] != self.user.id:
            # ret['url'] = f'http://localhost:8000/food/group-recipe/{ret["user"]}/{ret["slug"]}'
            ret['url'] = reverse("recipe:recipe-detail", kwargs={
                                 'slug': ret['slug']}, request=self.context['request']) + f"?user={ret['user']}"
        return ret

    def to_internal_value(self, data):
        """ create ingredient if does not exists in database """
        new_ingredients = data.get('new_ingredients', None)
        if new_ingredients:
            for items_list in new_ingredients:
                ingredient = items_list['ingredient']

                try:
                    obj, created = Ingredient.objects.get_or_create(user=self.user,
                                                                    **ingredient)
                except (TypeError, FieldError):
                    raise serializers.ValidationError({'ingredients': 'Invalid request \
                    structure for ingredients. Valid structure: {"ingredients":\
                    ["ingredient: slug, amount, unit"]} '})

                if created:
                    items_list.update({'ingredient': obj.slug})
        return super().to_internal_value(data)

        #     for list_item in new_ingredients:
        #         try:
        #             name = list_item['ingredient']
        #             obj, created = Ingredient.objects.get_or_create(user=self.user,
        #                                                             name=name)
        #         except TypeError:
        #             raise serializers.ValidationError({'ingredients': 'Invalid request \
        #             structure for ingredients. Valid structure: {"ingredients":\
        #             ["ingredient: slug, amount, unit"]} '})
        #
        #         if created:
        #             list_item.update({'ingredient': obj.slug})
        # return super().to_internal_value(data)

    def validate_name(self, value):
        """ check if recipe with provided name is not already in db """

        queryset = Recipe.objects.filter(user=self.user).filter(name=value)
        check_if_name_is_in_db(self.instance, queryset)

        return value

    def create(self, validated_data):
        """ Overrided for neasted serializers handling """
        validated_ingredients = validated_data.pop(
            'ingredients_quantity', None)
        recipe = super().create(validated_data)
        if validated_ingredients:
            for ingredient in validated_ingredients:
                Recipe_Ingredient.objects.create(
                    recipe=recipe,
                    **ingredient
                )
        return recipe

    def __init__(self, *args, **kwargs):
        """ get user from context """
        super().__init__(*args, **kwargs)
        try:
            self.user = self.context['user']
        except KeyError:
            self.user = None


class RecipeDetailSerializer(RecipeSerializer):
    """ Serializer for recipe detail, only for retrieve """

    ingredients = RecipeIngredientSerializer(many=True, write_only=False,
                                             source='ingredients_quantity',
                                             required=False
                                             )

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('user', 'slug', 'photo1', 'photo2', 'photo3',
                            'proteins', 'carbohydrates', 'fats', 'calories')

    def update(self, instance, validated_data):
        """ Overrided for neasted serializers handling """

        validated_ingredients = validated_data.pop(
            'ingredients_quantity', None)
        recipe = super().update(instance, validated_data)

        if getattr(self.root, 'partial', False) is False:
            """ we need to remove all related field during full update to
             support ingredients changes """

            instance.ingredients.clear()

        if validated_ingredients:
            for ingredient in validated_ingredients:
                ingredient.update({'recipe': recipe})
                recipe.ingredients.add(ingredient['ingredient'],
                                       through_defaults={'amount':
                                                         ingredient['amount'],
                                                         'unit': ingredient['unit']})
        return recipe


class RecipeImageSerializer(serializers.ModelSerializer):
    """ Serializer for uploading images to recipes """

    class Meta:
        model = Recipe
        fields = ('slug', 'photo1', 'photo2', 'photo3')
        read_only_fields = ('slug', )
