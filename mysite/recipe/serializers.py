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
        queryset=Tag.objects.all()
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

    ingredient = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = Recipe_Ingredient
        fields = ('ingredient', 'quantity')


class RecipeSerializer(serializers.ModelSerializer):
    """ serializer for recipe objects """

    tag = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Tag.objects.all()
    )

    ingredients = RecipeIngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'user', 'name', 'calories',
                  'portions', 'prepare_time', 'ingredients', 'tag',
                  'description',)
        read_only_fields = ('id', 'user', )

    def validate_name(self, value):
        """ check if recipe with provided name is not already in db """

        user = self.context['request'].user

        queryset = Recipe.objects.filter(user=user).filter(name=value)
        check_if_name_is_in_db(self.instance, queryset)

        return value

    def validate_ingredient(self, attrs):
        print("jestem tutaj")

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        ingredients_raw = data.get('ingredients')
        ingredients = self.validate_ingredient(ingredients_raw)
        internal_value.update(
            {'ingredients': ingredients}
        )
        return internal_value

    def create(self, validated_data):
        print(validated_data)


class RecipeDetailSerializer(RecipeSerializer):
    """ serializer a recipe detail """
    ingredient = IngredientSerializer(many=True, read_only=True)
    tag = TagSerializer(many=True, read_only=True)
