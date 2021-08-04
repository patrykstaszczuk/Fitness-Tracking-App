from rest_framework import serializers
from meals_tracker import models
from rest_framework.reverse import reverse
from recipe.models import Recipe, Ingredient
from recipe.serializers import UnitSerializer


class DatesSerializer(serializers.Serializer):
    """ simple serializer for dates """

    date = serializers.DateField()
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        """ return url fro specific date """
        url = reverse('meals_tracker:meal-list', request=self.request) \
            + "?date=" + str(obj['date'])
        return url

    def __init__(self, *args, **kwargs):
        """ pop request from kwargs """
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)


class MealCategorySerializer(serializers.ModelSerializer):
    """ serializer for MealCategory model """

    class Meta:
        model = models.MealCategory
        fields = '__all__'


class RecipePortionSerializer(serializers.ModelSerializer):
    """ serializer for meal-recipe extra info """

    class Meta:
        model = models.RecipePortion
        fields = ('recipe', 'portion')


class IngredientAmountSerializer(serializers.ModelSerializer):
    """ serializer for meal-ingredient extra info """

    class Meta:
        model = models.IngredientAmount
        fields = ('ingredient', 'unit', 'amount')


class RetrieveRecipeSerializer(serializers.ModelSerializer):
    """ serializer for retrieving recipe assigned to meal during meals GET
    action """

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


class RetrieveIngredientSerializer(serializers.ModelSerializer):
    """ serialzier for retrieving ingredients assigned to meal durign meals
    GET action """

    url = serializers.HyperlinkedIdentityField(view_name='recipe:ingredient-detail',
                                               lookup_field='slug')
    unit = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ('url', 'name', 'unit', 'amount')

    def get_unit(self, obj):
        """ return unit used to define ingredient amount """
        unit = models.IngredientAmount.objects.get(ingredient=obj, meal=self.meal).unit
        return UnitSerializer(unit).data

    def get_amount(self, obj):
        """ return amount of ingredient """
        amount = models.IngredientAmount.objects.get(ingredient=obj, meal=self.meal).amount
        return amount

    def __init__(self, *args, **kwargs):
        """ assigned meal instance to variable """
        super().__init__(*args, **kwargs)
        self.meal = self.context.get('meal_instance')


class MealsTrackerSerializer(serializers.ModelSerializer):
    """ serializer for meal objects """

    recipes = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name='meals_tracker:meal-detail')
    category = MealCategorySerializer(read_only=True)

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

        data = RetrieveRecipeSerializer(recipes,
                                        context={'request': request,
                                        'meal_instance': obj},
                                        read_only=True, many=True).data

        return data

    def get_ingredients(self, obj):
        """ get ingredient and extra information """

        ingredients = obj.ingredients.all()
        try:
            request = self.context['request'] # for API testing only
        except KeyError:
            request = None
        data = RetrieveIngredientSerializer(ingredients,
                                            context={'request': request,
                                            'meal_instance': obj},
                                            read_only=True, many=True).data
        return data


class CreateUpdateMealSerializer(MealsTrackerSerializer):
    """ serializer for meal creation """

    recipes = RecipePortionSerializer(write_only=True, required=False,
                                      many=True)
    ingredients = IngredientAmountSerializer(write_only=True, required=False,
                                             many=True)
    category = serializers.PrimaryKeyRelatedField(queryset=models.MealCategory.objects.all())

    def _validate_objects_permission(self, list_of_obj, entity):
        if list_of_obj:
            for item in list_of_obj:
                if item[f"{entity}"].user != self.context['request'].user:
                    raise serializers.ValidationError(f'No such {entity}')

    def is_valid(self, raise_exception=False):
        """ check if recipe is created by requested user """
        super().is_valid(raise_exception)
        recipes = self.validated_data.get('recipes', None)
        ingredients = self.validated_data.get('ingredients', None)
        if recipes:
            self._validate_objects_permission(recipes, "recipe")
        if ingredients:
            self._validate_objects_permission(ingredients, "ingredient")
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
        ingredients = self.get_ingredients(instance)
        ret['ingredients'] = ingredients
        ret['recipes'] = recipes
        return ret

    def create(self, validated_data):
        """ add recipes to meal with extra data """

        recipes = validated_data.pop('recipes', None)
        ingredients = validated_data.pop('ingredients', None)

        self.instance = super().create(validated_data)

        if recipes:
            for recipe in recipes:
                self.instance.recipes.add(
                    recipe['recipe'],
                    through_defaults={'meal': self.instance,
                                      'portion': recipe['portion']}
                )

        if ingredients:
            for ingredient in ingredients:
                self.instance.ingredients.add(
                    ingredient['ingredient'],
                    through_defaults={'meal': self.instance,
                                      'unit': ingredient['unit'],
                                      'amount': ingredient['amount']}
                )

        return self.instance

    def update(self, instance, validated_data):
        """ set the calories amount of meal to 0 during update """

        instance.calories = 0

        recipes = validated_data.pop('recipes', None)
        ingredients = validated_data.pop('ingredients', None)

        if getattr(self.root, 'partial', False) is False:
            """ clear all relationships if full update"""
            self.instance.recipes.clear()
            self.instance.ingredients.clear()
        instance = self._save_nested_relationships(instance, recipes,
                                                   ingredients)
        return super().update(instance, validated_data)

    def _save_nested_relationships(self, instance, recipes, ingredients):
        """ save nested realionships """
        if recipes:
            new_recipes = []
            for recipe in recipes:
                recipe['meal'] = instance
                if recipe['recipe'] in instance.recipes.all():
                    """ if there is such relation, update it """
                    models.RecipePortion.objects \
                        .filter(recipe=recipe['recipe'], meal=recipe['meal']).update(**recipe)
                else:
                    new_recipes.append(instance.recipes.through(**recipe))
            if new_recipes:
                instance.recipes.through.objects.bulk_create(new_recipes)
        if ingredients:
            new_ingredients = []
            for ingredient in ingredients:
                ingredient['meal'] = instance
                if ingredient['ingredient'] in instance.ingredients.all():
                    models.IngredientAmount.objects.filter(ingredient=ingredient['ingredient'],
                                                  meal=instance).update(**ingredient)
                else:
                    new_ingredients.append(instance.ingredients.through(**ingredient))
            if new_ingredients:
                instance.ingredients.through.objects.bulk_create(new_ingredients)
        return instance
