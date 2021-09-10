from typing import Iterable
from .models import HealthDiary
from django.db import models
from django.contrib.auth import get_user_model
import datetime

def get_health_diaries(user: get_user_model, date=None) -> Iterable[HealthDiary]:
    """ return health diaries instances for given user and date (if not None) """

    if date:
        
        obj, created = HealthDiary.objects.get_or_create(user=user, date=date)


    return HealthDiary.objects.all().filter(user=user, date=date)

def get_fields_usable_for_calculations() -> models:
    """ get field which can be use for calculations """
    usable_fields = []
    all_fields = HealthDiary._meta.get_fields()
    approved_field_types = (models.FloatField, models.PositiveIntegerField,
                            models.SmallIntegerField, models.PositiveSmallIntegerField)
    for field in all_fields:
        if isinstance(field, approved_field_types):
            usable_fields.append(field)
    return usable_fields