import datetime
import time

from django.db import models
from django.utils.text import slugify
from django.conf import settings


class HealthDiary(models.Model):

    date = models.DateField(default=datetime.date.today)
    slug = models.SlugField(blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.PROTECT)
    weight = models.FloatField(null=True, blank=True, default=None,
                               verbose_name='weigth')
    sleep_length = models.TimeField(null=True, blank=True)
    rest_heart_rate = models.PositiveSmallIntegerField(
        null=True, blank=True, default=0, verbose_name='heart rate')
    calories = models.PositiveIntegerField(blank=True, default=0,
                                           verbose_name='calories')
    burned_calories = models.PositiveSmallIntegerField(blank=True, default=0)
    last_update = models.PositiveIntegerField(default=time.time)
    daily_thoughts = models.TextField(
        max_length=2000, blank=True, null=True)

    def __str__(self):
        return self.user.name + ' ' + str(self.date)

    class Meta:
        unique_together = ('date', 'user')

    def save(self, *args, **kwargs):
        """ override for slug creation """
        if not self.id:
            self.slug = slugify(self.date)
        super().save(*args, **kwargs)

    def clean(self):
        """ make sure sleep length is in proper format """

        if isinstance(self.sleep_length, str):
            self.sleep_length = datetime.strptime(
                self.sleep_length, '%H:%M:%S')
