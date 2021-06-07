from django.db import models
from django.conf import settings
import datetime

from recipe.models import Recipe
# Create your models here.


class Meal(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    date = models.DateField(default=datetime.date.today)
    name = models.CharField(max_length=50, blank=False)
    calories = models.PositiveSmallIntegerField(null=False, blank=True,
                                                default=None)
    recipes = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        """ string representation """
        return f'{self.user} + {self.date} + {self.name}'
