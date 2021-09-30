from rest_framework.serializers import RelatedField
from django.urls import reverse
from recipe import selectors


class CustomRecipePortionField(RelatedField):
    """ custom tag field represented tag by id and name """

    def to_representation(self, value):
        portion = value.recipeportion_set.get(
            meal=self.root.instance.first()).portion
        calories = selectors.recipe_calculate_calories_based_on_portion(
            portion, value)

        recipe = {
            'id': value.id,
            'name': value.name,
            'slug': value.slug,
            'portion': portion,
            'calories': calories
        }
        return recipe


class CustomIngredientAmountField(RelatedField):
    """ custom tag field represented tag by id and name """

    def to_representation(self, value):
        ingredient = {
            'id': value.id,
            'slug': value.slug,
            'name': value.name
        }
        return ingredient
