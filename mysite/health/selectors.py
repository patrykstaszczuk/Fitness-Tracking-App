from typing import Iterable
import datetime

from django.db import models
from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from health.models import HealthDiary


def health_diary_get(user: get_user_model, date: datetime) -> HealthDiary:
    validate_date(date)
    obj, created = HealthDiary.objects.get_or_create(user=user, date=date)
    return obj


def health_diary_list(user: get_user_model) -> Iterable[HealthDiary]:
    return HealthDiary.objects.filter(user=user).order_by('-date')


def validate_date(date: str) -> None:
    if isinstance(date, str):
        try:
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError(
                'Invalid date format, It must be in YYYY-MM-DD format')
    if date > datetime.date.today():
        raise ValidationError(
            f'You cannot add statistics to diary in the future')


def get_all_values_for_given_field(user: get_user_model, slug: str) -> HealthDiary:
    """ return all values for given field name and user """
    field_name = _map_slug_to_health_diary_field(slug)
    return HealthDiary.objects.filter(user=user).values(field_name)


def _map_slug_to_health_diary_field(slug: str) -> str:
    """ map verbose name of field to model field name and return it """
    approved_fields = _get_fields_allowed_for_calculations()
    for field in approved_fields:
        if slug in [field.name, field.verbose_name]:
            return field.name
    raise ValidationError(f'{slug} field not allowed as slug')


def _get_fields_allowed_for_calculations() -> list[models]:
    """ return only that fields which are allwod for calculations  """
    allowed_fields_types = (models.FloatField, models.PositiveIntegerField,
                            models.SmallIntegerField, models.PositiveSmallIntegerField, models.TimeField)
    ommited_fields = ['last_update']
    all_fields = HealthDiary._meta.get_fields()
    allowed_fields = []
    for field in all_fields:
        if isinstance(field, allowed_fields_types) and field.name not in ommited_fields:
            allowed_fields.append(field)
    return allowed_fields


def get_weekly_avg_stats(user: get_user_model) -> dict:
    """ return avarage values for statistics """
    week_ago_date = datetime.date.today() - datetime.timedelta(days=7)
    stats = HealthDiary.objects.filter(user=user).filter(date__gte=week_ago_date).aggregate(
        weight=Avg('weight'),
        rest_heart_rate=Avg('rest_heart_rate'),
        sleep_length=Avg('sleep_length'),
        calories=Avg('calories'),
        burned_calories=Avg('burned_calories'),
        )
    return stats
