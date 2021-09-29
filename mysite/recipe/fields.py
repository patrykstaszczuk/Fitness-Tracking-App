from rest_framework.serializers import RelatedField
from django.urls import reverse
from recipe.selectors import ingredient_calculate_calories


class CustomTagField(RelatedField):
    """ custom tag field represented tag by id and name """

    def to_representation(self, value):
        tag = {
            'id': value.id,
            'slug': value.slug,
            'name': value.name
        }
        return tag


class CustomIngredientField(RelatedField):
    """ custom ingredient field with extra information about amount of unit """

    def to_representation(self, value):
        try:
            unit = value.recipe_ingredient_set.all()[0].unit
            amount = value.recipe_ingredient_set.all()[0].amount
            calories = ingredient_calculate_calories(value, unit, amount)
        except AttributeError:
            unit = None
            amount = None
            calories = None

        unit_name = None
        if unit:
            unit_name = unit.name

        ingredient = {
            'id': value.id,
            'slug': value.slug,
            'name': value.name,
            'calories': calories,
            'unit': unit_name,
            'amount': amount,
        }
        return ingredient


# class CustomUnitField(RelatedField):
#     """ custom unit-ingredient mapping field """
#
#     def to_representation(self, value):
#         tag = {
#             'id': value.id,
#             'name': value.name
#         }
#         return tag
