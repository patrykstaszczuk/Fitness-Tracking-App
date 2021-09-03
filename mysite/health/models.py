from django.db import models
from django.contrib.auth import get_user_model
import datetime
import time
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
                               verbose_name='weigth')
    sleep_length = models.FloatField(null=True, blank=True, default=None,
                                     verbose_name='sleep')
    rest_heart_rate = models.PositiveSmallIntegerField(null=True, blank=True,
                                                       default=None,
                                                       verbose_name='heart rate')
    calories = models.PositiveIntegerField(blank=True, default=0,
                                           verbose_name='calories')
    burned_calories = models.PositiveSmallIntegerField(blank=True, default=0)
    last_update = models.PositiveIntegerField(default=time.time())
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
        all_meals = Meal.objects.filter(user=self.user, date=self.date)
        calories = 0
        for meal in all_meals:
            calories += meal.calories
        return calories

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = datetime.date.today()
        if hasattr(self, 'id') and self.date == today:
            self.calories = self._recalculate_calories()
            # self.burned_calories = self._get_burned_calories()
