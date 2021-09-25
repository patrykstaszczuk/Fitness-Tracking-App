from rest_framework.serializers import RelatedField
from django.urls import reverse


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
        ingredient = {
            'id': value.id,
            'slug': value.slug,
            'name': value.name,
            'calories': value.calories,
            'unit': value.recipe_ingredient_set.all()[0].unit.name,
            'amount': value.recipe_ingredient_set.all()[0].amount
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
