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

    ingredient = serializers.SlugRelatedField(
            queryset=Ingredient.objects.all(),
            slug_field='slug',
            required=False
    )

    class Meta:
        model = Recipe_Ingredient
        fields = ('ingredient', 'quantity')
        extra_kwargs = {'recipe': {'write_only': True}, 'quantity':
                        {'required': False},
                        }


class RecipeSerializer(serializers.ModelSerializer):
    """ serializer for recipe objects """

    tags = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=Tag.objects.all(),
        required=True
    )
    ingredients = RecipeIngredientSerializer(required=False,
                                             many=True,
                                             write_only=True,
                                             source='ingredients_quantity')

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('id', 'user', 'slug')
        extra_kwargs = {
            'calories': {'write_only': True},
            'portions': {'write_only': True},
            'prepare_time': {'write_only': True},
            'description': {'write_only': True}
        }

    def validate_name(self, value):
        """ check if recipe with provided name is not already in db """

        user = self.context['request'].user

        queryset = Recipe.objects.filter(user=user).filter(name=value)
        check_if_name_is_in_db(self.instance, queryset)

        return value

    def validate_ingredients(self, value):
        """ placeholder for nested ingredients field validation """
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients_quantity', None)
        recipe = super().create(validated_data)

        if ingredients:
            for ingredient in ingredients:
                Recipe_Ingredient.objects.create(
                    recipe=recipe,
                    **ingredient
                )
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients_quantity', None)
        recipe = super().update(instance, validated_data)
        existing_recipe_ingredient_rows = Recipe_Ingredient.objects. \
            filter(recipe=recipe)
        for rows in existing_recipe_ingredient_rows:
            rows.delete()
        if ingredients:
            for ingredient in ingredients:
                ingredient.update({'recipe': recipe})
                obj = Recipe_Ingredient.objects.create(**ingredient)
                print(recipe.ingredients.all())
        return recipe


class RecipeDetailSerializer(RecipeSerializer):
    """ serializer a recipe detail """

    ingredients = RecipeIngredientSerializer(many=True, write_only=False,
                                             source='ingredients_quantity')

    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('id', 'user', 'slug')
