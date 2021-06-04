from django.db import models
from django.contrib.auth import get_user_model
import datetime
from django.utils.text import slugify
from django.conf import settings
# Create your models here.


class HealthDiary(models.Model):

    date = models.DateField(default=datetime.date.today)
    slug = models.SlugField(blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    weight = models.FloatField(null=True, blank=True, default=None)
    sleep_length = models.FloatField(null=True, blank=True, default=None)
    rest_heart_rate = models.PositiveSmallIntegerField(null=True, blank=True,
                                                       default=None)
    calories = models.PositiveIntegerField(null=True, blank=True, default=None)
    daily_thoughts = models.TextField(max_length=2000, blank=True)

    def __str__(self):
        return self.user.name + ' ' + str(self.date)

    class Meta:
        unique_together = ('date', 'user')

    def save(self, *args, **kwargs):
        """ override for slug creation """
        self.slug = slugify(self.date)
        super().save(*args, **kwargs)
