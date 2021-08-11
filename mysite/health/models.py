from django.db import models
from django.contrib.auth import get_user_model
import datetime
from django.utils.text import slugify
from django.conf import settings
from meals_tracker.models import Meal
# Create your models here.



def get_health_model_usable_fields():
    """ get field which can be use for analysis """
    usable_fields = []
    all_fields = HealthDiary._meta.get_fields()
    approved_field_types = (models.FloatField, models.PositiveIntegerField,
                            models.SmallIntegerField, models.PositiveSmallIntegerField)
    for field in all_fields:
        if isinstance(field, approved_field_types):
            usable_fields.append(field)
    return usable_fields


class HealthDiary(models.Model):

    date = models.DateField(default=datetime.date.today)
    slug = models.SlugField(blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    weight = models.FloatField(null=True, blank=True, default=None,
                               verbose_name='waga')
    sleep_length = models.FloatField(null=True, blank=True, default=None,
                                     verbose_name='sen')
    rest_heart_rate = models.PositiveSmallIntegerField(null=True, blank=True,
                                                       default=None,
                                                       verbose_name='tetno')
    calories = models.PositiveIntegerField(blank=True, default=0,
                                           verbose_name='kalorie')
    daily_thoughts = models.TextField(max_length=2000, blank=True)

    def __str__(self):
        return self.user.name + ' ' + str(self.date)

    class Meta:
        unique_together = ('date', 'user')

    def save(self, *args, **kwargs):
        """ override for slug creation """
        if not self.id:
            self.slug = slugify(self.date)
        super().save(*args, **kwargs)

    def _recalculate_calories(self):
        """ recalculate calories based on meals """
        self.calories = 0
        all_meals = Meal.objects.filter(user=self.user, date=self.date)
        for meal in all_meals:
            self.calories = meal.calories

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'id'):
            self._recalculate_calories()
