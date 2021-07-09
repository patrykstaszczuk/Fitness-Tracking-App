from django.db import models
import datetime
from django.utils.text import slugify
from django.conf import settings
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
    calories = models.PositiveIntegerField(null=True, blank=True, default=None,
                                           verbose_name='kalorie')
    daily_thoughts = models.TextField(max_length=2000, blank=True)

    def __str__(self):
        return self.user.name + ' ' + str(self.date)

    class Meta:
        unique_together = ('date', 'user')

    def save(self, *args, **kwargs):
        """ override for slug creation """
        self.slug = slugify(self.date)
        super().save(*args, **kwargs)
