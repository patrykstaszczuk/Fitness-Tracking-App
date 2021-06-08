from rest_framework import serializers
from meals_tracker import models

from recipe.models import Recipe


class RecipeHelperSerializer(serializers.ModelSerializer):
    """ nested serializer for specific recipe information needed for meal """

    class Meta:
        model = Recipe
        fields = ('slug', 'name', 'calories')


class MealsTrackerSerializer(serializers.ModelSerializer):
    """ serializer for meal objects """

    recipe_detail = RecipeHelperSerializer(source='recipe', read_only=True)

    class Meta:
        model = models.Meal
        fields = ('user', 'date', 'calories', 'category', 'recipe',
                  'recipe_detail')
        read_only_fields = ('id', 'user', 'date')
