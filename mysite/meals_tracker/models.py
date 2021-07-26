from django.db import models
from django.conf import settings
import datetime
from django.dispatch import receiver
from django.db.models.signals import m2m_changed, post_save
from django.core.exceptions import ValidationError

from recipe.models import Recipe, Ingredient, Unit
# Create your models here.


class Meal(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    date = models.DateField(default=datetime.date.today)
    # name = models.CharField(max_length=50, blank=False)
    calories = models.PositiveSmallIntegerField(null=False, blank=True,
                                                default=0)
    category = models.ForeignKey('MealCategory', on_delete=models.PROTECT,
                                 null=False, related_name='meal', blank=False)
    recipes = models.ManyToManyField(Recipe, through='RecipePortion')
    ingredients = models.ManyToManyField(Ingredient, through='IngredientAmount')

    def __str__(self):
        """ string representation """
        return f'{self.user} + {self.date}'

    def set_calories(self):
        """ recalculate calories when m2m change or specific Recipe is being
            saved """
        self.calories = 0
        for recipe in self.recipes.all():
            obj = RecipePortion.objects.get(recipe=recipe, meal=self)
            if recipe.calories is not None:
                self.calories += recipe.get_calories(obj.portion)

    def save(self, *args, **kwargs):
        """ initiate set_calories method """
        super().save(*args, **kwargs)
        self.set_calories()
        kwargs['force_insert'] = False
        super().save(*args, **kwargs, update_fields=['calories', ])


class RecipePortion(models.Model):
    """ Intermediate table for Meal - Recipe """

    meal = models.ForeignKey(Meal, on_delete=models.CASCADE,
                             related_name='recipes_extra_info', null=False)
    portion = models.PositiveSmallIntegerField(default=1)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, null=False)

    class Meta:
        constraints = [
             models.UniqueConstraint(fields=['meal', 'recipe'],
                                     name='unique recipe-meal')
        ]

    def __str__(self):
        return str(self.portion)


class IngredientAmount(models.Model):
    """ Intermediate table for Meal - Ingredient """

    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, null=False)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=False)
    amount = models.PositiveSmallIntegerField(null=False)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   null=False)


class MealCategory(models.Model):

    name = models.CharField(max_length=20, null=False, unique=True)

    def __str__(self):
        """ string representation """
        return self.name


@receiver(post_save, sender=Recipe)
@receiver(m2m_changed, sender=RecipePortion)
def _recalculate_total_meal_calories(sender, instance, action=None, **kwargs):
    """ call Meal instance function to recalculate calories """
    if sender == RecipePortion and action == 'post_add':
        instance.save()
    elif sender == Recipe:
        meals = Meal.objects.filter(recipes=instance.id)
        for meal in meals:
            meal.save()
