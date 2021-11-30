# from django.db.models.signals import m2m_changed, post_save
# from django.dispatch import receiver
# from recipe.models import Recipe
# from meals_tracker.models import RecipePortion, IngredientAmount, Meal
# from meals_tracker.services import MealService
#
#
# @receiver(post_save, sender=Recipe)
# @receiver(m2m_changed, sender=RecipePortion)
# @receiver(m2m_changed, sender=IngredientAmount)
# def _recalculate_total_meal_calories(sender, instance, action=None, **kwargs):
#     """ call Meal instance function to recalculate calories """
#     if (sender in [RecipePortion, IngredientAmount]) and action == 'post_add':
#         MealService.recalculate_total_meal_calories(meal=instance)
#     elif sender == Recipe:
#         meals = Meal.objects.filter(recipes=instance.id)
#         for meal in meals:
#             MealService.recalculate_total_meal_calories(meal=meal)
