from .models import HealthDiary
from django.db import models

def get_health_diaries(detail=None)
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