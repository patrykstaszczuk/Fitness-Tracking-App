from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from .models import Ingredient, Recipe_Ingredient, Recipe, Unit
from recipe import services, selectors


@receiver(post_save, sender=Recipe)
@receiver(post_save, sender=Ingredient)
@receiver(m2m_changed, sender=Recipe_Ingredient)
def _count_calories_based_on_ingredients(sender, instance, action=None,
                                         **kwargs):
    """ sum up calories from all recipe ingredients """
    if action in ['post_add', 'post_remove', 'post_clear']:
        services.RecipeService.recalculate_nutritions_values(recipe=instance)
        # services.recalculate_nutritions_values(recipe=instance)
    elif sender == Ingredient:
        recipes = Recipe.objects.filter(ingredients=instance.id).prefetch_related(
            'ingredients', 'ingredient__recipe_ingredient_set')
        for recipe in recipes:
            services.RecipeService.recalculate_nutritions_values(
                recipe=instance)
            # services.recalculate_nutritions_values(recipe=recipe)
            # recipe._recalculate_nutritions_values()


# @receiver(post_save, sender=Ingredient)
# def _add_default_unit_for_ingredient(sender, instance, action=None, **kwargs):
#     """ add default unit for new ingredient """
#     gram_unit_instance, created = selectors.unit_get(id=None, default=True)
#     if created:
#         data = {
#             'units': [{'unit': gram_unit_instance, 'grams_in_one_unit': 100}]}
#         ingredient_service = services.IngredientService(
#             user=instance.user, data=data)
#         ingredient_service.save_m2m_fields(instance)
#         ingredient_service.save_m2m_fields(instance)
#         ingredient_service.save_m2m_fields(instance)
