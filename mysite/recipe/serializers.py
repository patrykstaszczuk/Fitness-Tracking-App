from rest_framework import serializers
from recipe.models import Ingredient, Tag, Recipe, Recipe_Ingredient


def raise_validation_error(instance):
    raise serializers.ValidationError('Ta nazwa jest już zajęta !')


def check_if_name_is_in_db(instance, queryset):
    if instance is None:
        if queryset.exists():
            raise_validation_error(instance)
    else:
        if queryset.exclude(id=instance.id):
            raise_validation_error(instance)


class IngredientSerializer(serializers.ModelSerializer):
    """ Serializer for ingredient objects """
    tag = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Tag.objects.all(),
        required=False
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'slug', 'user', 'tag')
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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """ serializer for intermediate model for recipe and ingredient, with
        field quantity """

    ingredient = serializers.PrimaryKeyRelatedField(
            queryset=Ingredient.objects.all(),
            required=False
    )

    class Meta:
        model = Recipe_Ingredient
        fields = ('ingredient', 'quantity')
        extra_kwargs = {'recipe': {'write_only': True}, 'quantity':
                        {'required': False}}


class RecipeSerializer(serializers.ModelSerializer):
    """ serializer for recipe objects """

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=False
    )
    ingredients = RecipeIngredientSerializer(required=False,
                                             many=True)

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('id', 'user', 'slug')

    def validate_name(self, value):
        """ check if recipe with provided name is not already in db """

        user = self.context['request'].user

        queryset = Recipe.objects.filter(user=user).filter(name=value)
        check_if_name_is_in_db(self.instance, queryset)

        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)

        for ingredient in ingredients:
            Recipe_Ingredient.objects.create(
                recipe=recipe,
                **ingredient
            )
        return recipe


class RecipeDetailSerializer(RecipeSerializer):
    """ serializer a recipe detail """
    ingredient = RecipeIngredientSerializer(many=True, read_only=True)
    tag = TagSerializer(many=True, read_only=True)
