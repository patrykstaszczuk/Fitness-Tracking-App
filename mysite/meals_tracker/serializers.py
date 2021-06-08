from rest_framework import serializers
from meals_tracker import models

from recipe.models import Recipe


class RecipeHelperSerializer(serializers.ModelSerializer):
    """ nested serializer for specific recipe information needed for meal """

    class Meta:
        model = Recipe
        fields = ('slug', 'name', 'calories', 'portions')


class MealsTrackerSerializer(serializers.ModelSerializer):
    """ serializer for meal objects """

    recipe_detail = RecipeHelperSerializer(source='recipe', read_only=True)

    class Meta:
        model = models.Meal
        fields = ('user', 'date', 'calories', 'category', 'recipe',
                  'recipe_detail', 'recipe_portions')
        read_only_fields = ('id', 'user', 'date', 'calories')

    def validate(self, values):
        """ overall validation of serializers fields """

        if values.get('recipe') and not values.get('recipe_portions'):
            raise serializers.ValidationError('Chose portions for given recipe')
        elif values.get('recipe_portions') and not values.get('recipe'):
            raise serializers.ValidationError('Choose recipe for given portions')
        return values
