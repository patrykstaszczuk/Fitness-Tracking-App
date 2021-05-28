from django.db import models
from django.contrib.auth import get_user_model
import datetime
# Create your models here.


class HealthDiary(models.Model):

    date = models.DateField(default=datetime.date.today)
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    weight = models.FloatField(null=True, blank=True)
    sleep_length = models.FloatField(null=True, blank=True)
    rest_heart_rate = models.PositiveSmallIntegerField(null=True, blank=True)
    calories = models.PositiveIntegerField(null=True, blank=True)
    daily_thoughts = models.TextField(max_length=2000, blank=True)

    def __str__(self):
        return self.user.name + ' ' + str(self.date)

    class Meta:
        unique_together = ('date', 'user')
