from rest_framework import serializers
from meals_tracker.models import Meal, MealCategory
from rest_framework.reverse import reverse
from mysite import serializers as generic_serializers
from meals_tracker.fields import CustomRecipePortionField, CustomIngredientAmountField


class MealOutputSerializer(serializers.ModelSerializer):
    """ serializing outcomming data for Meal model """

    recipes = CustomRecipePortionField(many=True, read_only=True)
    ingredients = CustomIngredientAmountField(many=True, read_only=True)

    class Meta:
        model = Meal
        fields = '__all__'

    def to_representation(self, instance):
        """ append url for recipes and ingredients """
        ret = super().to_representation(instance)
        for recipe in ret['recipes']:
            url = reverse('recipe:recipe-detail', request=self.context['request'],
                          kwargs={'slug': recipe['slug']})
            recipe['url'] = url
        for ingredient in ret['ingredients']:
            url = reverse('recipe:ingredient-detail', request=self.context['request'],
                          kwargs={'slug': ingredient['slug']})
            ingredient['url'] = url
        return ret


class MealCreateInputSerializer(serializers.Serializer):
    """ serialing input data for Meal creation """

    category = serializers.IntegerField(required=True)
    recipes = generic_serializers.inline_serializer(many=True, required=False, fields={
        'recipe': serializers.IntegerField(required=True),
        'portion': serializers.IntegerField(required=True, min_value=1)
    })
    ingredients = generic_serializers.inline_serializer(many=True, required=False, fields={
        'ingredient': serializers.IntegerField(required=True),
        'unit': serializers.IntegerField(required=True),
        'amount': serializers.IntegerField(required=True)
    })


class MealUpdateInputSerializer(MealCreateInputSerializer):
    """ serializing input data during update with no required fields """
    category = serializers.IntegerField(required=False)


class MealDateOutputSerializer(serializers.Serializer):
    """ serializer for Meal dates only """

    date = serializers.DateField()


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


class MealCategoryOutputSerializer(serializers.ModelSerializer):
    """ serializing MealCategory  objects """

    class Meta:
        model = MealCategory
        fields = '__all__'
