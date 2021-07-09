from django.db import models
from django.conf import settings
import datetime

from django.core.exceptions import ValidationError

from recipe.models import Recipe
# Create your models here.


class Meal(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    date = models.DateField(default=datetime.date.today)
    # name = models.CharField(max_length=50, blank=False)
    calories = models.PositiveSmallIntegerField(null=False, blank=True,
                                                default=0)
    category = models.ForeignKey('MealCategory', on_delete=models.PROTECT,
                                 null=False, related_name='meal', blank=False)
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True,
                               blank=True)
    recipe_portions = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        """ string representation """
        return f'{self.user} + {self.date}'

    def save(self, *args, **kwargs):
        """ set calories based on provided recipe, ingredients or ready
        meals """
        self.full_clean()
        if self.calories is None:
            self.calories = 0

        if self.recipe:
            self.calories += self.recipe.get_calories(self.recipe_portions)
        super().save(*args, **kwargs)

    def clean(self):
        """ check if recipe and recipe_portions are set or not set together """
        if self.recipe is None:
            assert self.recipe_portions is None, "Recipe should be set"
        if self.recipe is not None:
            assert self.recipe_portions is not None, "Portion should be set"


class MealCategory(models.Model):

    name = models.CharField(max_length=20, null=False)

    def __str__(self):
        """ string representation """
        return self.name
