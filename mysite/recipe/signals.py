from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from .models import Ingredient, Recipe_Ingredient, Recipe, Unit

@receiver(post_save, sender=Recipe)
@receiver(post_save, sender=Ingredient)
@receiver(m2m_changed, sender=Recipe_Ingredient)
def _count_calories_based_on_ingredients(sender, instance, action=None,
                                         **kwargs):
    """ sum up calories from all recipe ingredients """
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance._recalculate_nutritions_values()
    elif sender == Ingredient:
        recipes = Recipe.objects.filter(ingredients=instance.id)
        for recipe in recipes:
            recipe._recalculate_nutritions_values()

@receiver(post_save, sender=Ingredient)
def _add_default_unit_for_ingredient(sender, instance, action=None, **kwargs):
    """ add default unit for new ingredient """

    gram_unit_instance, crated = Unit.objects.get_or_create(name='gram')
    instance.units.add(gram_unit_instance,  through_defaults={'grams_in_one_unit': 100})
