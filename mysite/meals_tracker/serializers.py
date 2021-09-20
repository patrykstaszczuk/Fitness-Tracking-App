from rest_framework import serializers
from meals_tracker.models import Meal, MealCategory
from rest_framework.reverse import reverse
from mysite import serializers as generic_serializers


class MealOutputSerializer(serializers.ModelSerializer):
    """ serializing outcomming data for Meal model """

    class Meta:
        model = Meal
        fields = '__all__'


class MealInputSerializer(serializers.Serializer):
    """ serialing input data for Meal creation """

    category = serializers.IntegerField(required=False)
    recipes = generic_serializers.inline_serializer(many=True, required=False, fields={
        'recipe': serializers.IntegerField(required=True),
        'portion': serializers.IntegerField(required=True, min_value=1)
    })
    ingredients = generic_serializers.inline_serializer(many=True, required=False, fields={
        'ingredient': serializers.IntegerField(required=True),
        'unit': serializers.IntegerField(required=True),
        'amount': serializers.IntegerField(required=True)
    })


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
