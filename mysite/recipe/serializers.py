from rest_framework import serializers
from recipe.models import Ingredient, Tag, Recipe, Recipe_Ingredient, Unit
from rest_framework import fields


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


class TagSlugRelatedField(serializers.SlugRelatedField):
    """ Filter all returned slug tags by specific user """

    def get_queryset(self):
        user = self.context['request'].user
        queryset = Tag.objects.filter(user=user)
        return queryset


class IngredientSerializer(serializers.ModelSerializer):
    """ Serializer for ingredient objects """

    tag = TagSlugRelatedField(
        many=True,
        slug_field='name',
        required=False
    )

    class Meta:
        model = Ingredient
        exclude = ('_usage_counter', )
        read_only_fields = ('id', 'user', 'slug')

    def validate_name(self, value):
        """ check if ingredient with provided name is not already in db """
        user = self.context['request'].user

        queryset = Ingredient.objects.filter(user=user).filter(name=value)
        check_if_name_is_in_db(self.instance, queryset)

        return value


class TagSerializer(serializers.ModelSerializer):
    """ Serializer for tag objects """

    class Meta:
        model = Tag
        fields = ('id', 'user', 'slug', 'name')
        read_only_fields = ('id', 'user', 'slug')

    def validate_name(self, value):
        """ check if tag with provided name is not already in db """

        user = self.context['request'].user
        queryset = Tag.objects.filter(user=user).filter(name=value)
        check_if_name_is_in_db(self.instance, queryset)

        return value


class IngredientSlugRelatedField(serializers.SlugRelatedField):
    """ Filter all returned slug ingredients by specyfic user """

    def get_queryset(self):
        user = self.context['request'].user
        queryset = Ingredient.objects.filter(user=user)
        return queryset


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """ serializer for intermediate model for recipe and ingredient, with
        field quantity """

    ingredient = IngredientSlugRelatedField(
            slug_field='slug',
            required=True
    )

    class Meta:
        model = Recipe_Ingredient
        fields = ('ingredient', 'amount', 'unit')
        # extra_kwargs = {
        #                 'quantity': {'required': False},
        #                 }


class RecipeSerializer(serializers.ModelSerializer):
    """ serializer for recipe objects """

    tags = TagSlugRelatedField(
        many=True,
        slug_field='slug',
        required=True
    )
    ingredients = RecipeIngredientSerializer(
                                             required=False,
                                             many=True,
                                             write_only=True,
                                             source='ingredients_quantity',
                                             )

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('id', 'user', 'slug', 'photo1', 'photo2', 'photo3')
        extra_kwargs = {
            'calories': {'write_only': True},
            'portions': {'write_only': True},
            'prepare_time': {'write_only': True},
            'description': {'write_only': True}
        }

    def to_internal_value(self, data):
        """ create ingredient if does not exists in database """

        if data.get('ingredients', None) is not None:
            ingredients = data.get('ingredients')
            for list_item in ingredients:
                obj, created = Ingredient.objects.get_or_create(user=self.user,
                                                                name=list_item['ingredient'])
                if created:
                    list_item.update({'ingredient': obj.slug})
        return super().to_internal_value(data)

    def validate_name(self, value):
        """ check if recipe with provided name is not already in db """

        queryset = Recipe.objects.filter(user=self.user).filter(name=value)
        check_if_name_is_in_db(self.instance, queryset)

        return value

    def create(self, validated_data):
        """ Overrided for neasted serializers handling """
        validated_ingredients = validated_data.pop('ingredients_quantity', None)
        recipe = super().create(validated_data)
        if validated_ingredients:
            for ingredient in validated_ingredients:
                Recipe_Ingredient.objects.create(
                    recipe=recipe,
                    **ingredient
                )
        return recipe

    def update(self, instance, validated_data):
        """ Overrided for neasted serializers handling """

        validated_ingredients = validated_data.pop('ingredients_quantity', None)
        recipe = super().update(instance, validated_data)

        existing_through_table_rows = Recipe_Ingredient.objects. \
            filter(recipe=recipe)
        for rows in existing_through_table_rows:
            rows.delete()

        if validated_ingredients:
            for ingredient in validated_ingredients:
                ingredient.update({'recipe': recipe})
                recipe.ingredients.add(ingredient['ingredient'],
                                       through_defaults={'amount':
                                       ingredient['amount'],
                                       'unit': ingredient['unit']})
        return recipe

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('request'):
            self.user = self.context['request'].user


class RecipeDetailSerializer(RecipeSerializer):
    """ Serializer a recipe detail """

    ingredients = RecipeIngredientSerializer(many=True, write_only=False,
                                             source='ingredients_quantity',
                                             )

    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('id', 'user', 'slug', 'photo1', 'photo2', 'photo3')


class RecipeImageSerializer(serializers.ModelSerializer):
    """ Serializer for uploading images to recipes """

    class Meta:
        model = Recipe
        fields = ('slug', 'photo1', 'photo2', 'photo3')
        read_only_fields = ('slug', )


class UnitSerializer(serializers.ModelSerializer):
    """ serializer for Unit model """

    class Meta:
        model = Unit
        fields = '__all__'
