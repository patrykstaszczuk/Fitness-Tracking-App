from rest_framework import serializers
from meals_tracker import models

from recipe.models import Recipe


class RecipePortionSerializer(serializers.ModelSerializer):
    """ serializer for meal-recipe extra info """

    class Meta:
        model = models.RecipePortion
        fields = ('recipe', 'portion')


class RecipePortionCustomSerializer(serializers.ModelSerializer):

    portions = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name='recipe:recipe-detail',
                                               lookup_field='slug')

    class Meta:
        model = Recipe
        fields = ('url', 'name', 'portions')

    def get_portions(self, obj):
        """ get portion for given meal-recipe mapping """
        meal = self.context.get('meal_instance')
        try:
            return models.RecipePortion.objects.get(recipe=obj,
                                                    meal=meal).portion
        except models.RecipePortion.DoesNotExist:
            return None


class MealsTrackerSerializer(serializers.ModelSerializer):
    """ serializer for meal objects """

    recipes = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name='meals_tracker:meal-detail')

    class Meta:
        model = models.Meal
        fields = ('id', 'url', 'user', 'date', 'calories', 'category',
                  'recipes', 'ingredients')
        read_only_fields = ('id', 'user', 'date', 'calories')

    def get_recipes(self, obj):
        """ get recipe and extra information """

        recipes = obj.recipes.all()
        try:
            request = self.context['request'] # for API testing only
        except KeyError:
            request = None

        data = RecipePortionCustomSerializer(recipes,
                                             context={'request': request,
                                             'meal_instance': obj},
                                             read_only=True, many=True).data

        return data


class CreateUpdateMealSerializer(MealsTrackerSerializer):
    """ serializer for meal creation """

    recipes = RecipePortionSerializer(write_only=True, required=False,
                                      many=True)

    def is_valid(self, raise_exception=False):
        """ check if recipe is created by requested user """
        super().is_valid(raise_exception)
        recipes = self.validated_data.get('recipes', None)
        if recipes:
            for item in recipes:
                if item['recipe'].user != self.context['request'].user:
                    raise serializers.ValidationError('No such recipe')
        return True

    def to_internal_value(self, values):
        """ check json structure """

        initial_values = values
        data = super().to_internal_value(values)

        if initial_values.keys() != data.keys():
            raise serializers.ValidationError({'non-field-error':
                                              'Bad structure for json request'})
        return data

    def to_representation(self, instance):
        """ add recipes to response """
        ret = super().to_representation(instance)
        recipes = self.get_recipes(instance)
        ret['recipes'] = recipes
        return ret

    def create(self, validated_data):
        """ add recipes to meal with extra data """
        recipes = validated_data.pop('recipes')
        self.instance = super().create(validated_data)
        for recipe in recipes:
            meal = self.instance
            recipe.update({'meal': meal})
            models.RecipePortion.objects.create(**recipe)

        return self.instance

    def update(self, instance, validated_data):
        """ set the calories amount of meal to 0 during update """

        self.instance.calories = 0

        recipes = validated_data.pop('recipes', None)

        if recipes:
            if getattr(self.root, 'partial', False) is False:
                """ clear all relationships if full update"""
                self.instance.recipes.clear()

            new_objects = []
            for recipe in recipes:
                recipe['meal'] = self.instance
                if recipe['recipe'] in self.instance.recipes.all():
                    """ if there is such relation, update it """
                    models.RecipePortion.objects \
                        .filter(recipe=recipe['recipe'], meal=recipe['meal']).update(**recipe)
                else:
                    new_objects.append(self.instance.recipes.through(**recipe))
            if new_objects:
                self.instance.recipes.through.objects.bulk_create(new_objects)

        return super().update(instance, validated_data)
