from rest_framework import serializers
from rest_framework.reverse import reverse

from mysite import serializers as generic_serializers
from meals_tracker.models import Meal, MealCategory, RecipePortion, IngredientAmount
from recipe import selectors
from recipe.serializers import UnitOutputSerializer


class MealCategorySerializer(serializers.ModelSerializer):
    """ serializing MealCategory  objects """

    class Meta:
        model = MealCategory
        fields = '__all__'


class MealDetailSerializer(serializers.ModelSerializer):
    """ serializing meal object """

    self = serializers.HyperlinkedIdentityField(
        view_name='meals_tracker:meal-detail'
    )
    recipes = serializers.HyperlinkedIdentityField(
        view_name='meals_tracker:meal-recipes')
    ingredients = serializers.HyperlinkedIdentityField(
        view_name='meals_tracker:meal-ingredients')
    category = serializers.SerializerMethodField()

    class Meta:
        model = Meal
        fields = '__all__'

    def get_category(self, instance):
        serializer = MealCategorySerializer(instance.category)
        return serializer.data


class MealsListSerializer(serializers.ModelSerializer):
    """ serializer for list of meals """

    self = serializers.HyperlinkedIdentityField(
        view_name='meals_tracker:meal-detail'
    )

    class Meta:
        model = Meal
        fields = ('id', 'self', 'calories', 'category')


class MealCreateSerializer(serializers.Serializer):
    """ serialing input data for Meal creation """

    category = serializers.IntegerField(required=True)
    date = serializers.DateField(required=True)
    recipes = generic_serializers.inline_serializer(many=True, required=False, fields={
        'recipe': serializers.IntegerField(required=True),
        'portion': serializers.IntegerField(required=True, min_value=1)
    })
    ingredients = generic_serializers.inline_serializer(many=True, required=False, fields={
        'ingredient': serializers.IntegerField(required=True),
        'unit': serializers.IntegerField(required=True),
        'amount': serializers.IntegerField(required=True)
    })


class MealRecipesSerializer(serializers.ModelSerializer):
    """ serializer for RecipePortion model objects """

    class RecipePortionDetailHyperlink(serializers.HyperlinkedIdentityField):

        def get_url(self, obj, view_name, request, format):
            url_kwargs = {
                'pk': obj.meal_id,
                'recipe_pk': obj.recipe_id
            }
            return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    class RecipeDetailHyperLink(serializers.HyperlinkedIdentityField):

        def get_url(self, obj, view_name, request, format):
            url_kwargs = {
                'slug': obj.recipe.slug,
            }
            return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    self = RecipePortionDetailHyperlink(
        view_name='meals_tracker:meal-recipes-detail')
    recipe = RecipeDetailHyperLink(view_name='recipe:recipe-detail')
    calories = serializers.SerializerMethodField()

    class Meta:
        model = RecipePortion
        fields = ('id', 'self', 'portion', 'calories', 'recipe')

    def get_calories(self, instance):
        return selectors.recipe_calculate_calories_based_on_portion(
            instance.portion,
            instance.recipe)


class MealIngredientsSerializer(serializers.ModelSerializer):
    """ serializer for IngredientAmount model objects """
    class IngredientAmountDetailHyperLink(serializers.HyperlinkedIdentityField):

        def get_url(self, obj, view_name, request, format):
            url_kwargs = {
                'pk': obj.meal_id,
                'ingredient_pk': obj.ingredient.id,
            }
            return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    class IngredientDetailHyperLink(serializers.HyperlinkedIdentityField):

        def get_url(self, obj, view_name, request, format):
            url_kwargs = {
                'slug': obj.ingredient.slug,
            }
            return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    self = IngredientAmountDetailHyperLink(
        view_name='meals_tracker:meal-ingredients-detail')
    ingredient = IngredientDetailHyperLink(
        view_name='recipe:ingredient-detail')
    unit = serializers.SerializerMethodField()
    calories = serializers.SerializerMethodField()

    class Meta:
        model = IngredientAmount
        fields = ('id', 'self', 'ingredient', 'unit', 'amount', 'calories')

    def get_unit(self, instance):
        serializer = UnitOutputSerializer(instance.unit)
        return serializer.data

    def get_calories(self, instance):
        return selectors.ingredient_calculate_calories(
            instance.ingredient, instance.unit, instance.amount)


class AddRecipeToMealSerializer(serializers.Serializer):
    """ serializer for adding recipes to meal """

    recipes = generic_serializers.inline_serializer(many=True, required=True, fields={
        'recipe': serializers.IntegerField(required=True),
        'portion': serializers.IntegerField(required=True)
    })


class AddIngredientToMealSerializer(serializers.Serializer):
    """ serializer for adding ingredients to meal """
    ingredients = generic_serializers.inline_serializer(many=True, required=False, fields={
        'ingredient': serializers.IntegerField(required=True),
        'unit': serializers.IntegerField(required=True),
        'amount': serializers.IntegerField(required=True)
    })


class MealRecipeUpdateSerializer(serializers.Serializer):
    """ serializer for updating meal recipe """
    portion = serializers.IntegerField()


class MealIngredientUpdateSerializer(serializers.Serializer):
    """ serialzier for updating meal ingredient """

    unit = serializers.IntegerField()
    amount = serializers.IntegerField()


class DatesSerializer(serializers.Serializer):
    """ simple serializer for dates """

    date = serializers.SerializerMethodField()

    def get_date(self, obj):
        """ return url fro specific date """
        url = reverse('meals_tracker:meal-list', request=self.context['request']) \
            + "?date=" + str(obj['date'])
        return url
