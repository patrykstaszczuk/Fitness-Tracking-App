from rest_framework import serializers
from recipe.models import Ingredient, Tag, Recipe


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


class RecipeSerializer(serializers.ModelSerializer):
    """ serializer for recipe objects """

    # ingredient = serializers.PrimaryKeyRelatedfield(
    #     many=True,
    #     queryset=Ingredient.objects.all()
    # )

    tag = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ('id', 'user', 'name', 'calories',
                  'portions', 'prepare_time', 'tag', 'description')
        read_only_fields = ('id', 'user', )

    def validate_name(self, value):
        """ check if recipe with provided name is not already in db """

        user = self.context['request'].user

        queryset = Recipe.objects.filter(user=user).filter(name=value)
        check_if_name_is_in_db(self.instance, queryset)

        return value
