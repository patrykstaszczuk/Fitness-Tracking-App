from django.db import models
from django.conf import settings
import datetime

from recipe.models import Recipe
# Create your models here.


class Meal(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    date = models.DateField(default=datetime.date.today)
    # name = models.CharField(max_length=50, blank=False)
    calories = models.PositiveSmallIntegerField(null=False, blank=True,
                                                default=0)
    category = models.ForeignKey('MealCategory', on_delete=models.PROTECT,
                                 null=True, related_name='mea')
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        """ string representation """
        return f'{self.user} + {self.date}'

    def save(self, *args, **kwargs):
        """ set calories based on provided recipe, ingredients or ready
        meals """

        if self.calories is None:
            self.calories = 0

        if self.recipe:
            self.calories = self.calories + self.recipe.calories
        super().save(*args, **kwargs)


class MealCategory(models.Model):

    name = models.CharField(max_length=20, null=False)

    def __str__(self):
        """ string representation """
        return self.name
