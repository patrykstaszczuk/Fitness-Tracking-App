from typing import Iterable
from .models import HealthDiary
from django.db import models
from django.contrib.auth import get_user_model
from health import services
import datetime

def get_health_diary(user: get_user_model, date: datetime=datetime.date.today()) -> HealthDiary:
    """ return today'shealth diary instance for given user """
    obj, created = HealthDiary.objects.get_or_create(user=user, date=date)
    services.recalculate_total_calories_intake(instance=obj)
    obj.save()
    return obj

def get_health_diaries(user: get_user_model) -> Iterable[HealthDiary]:
    """ return health diaries instances for given user and date """
    return HealthDiary.objects.filter(user=user)

def get_all_values_for_given_field(user: get_user_model, field_name: str) -> HealthDiary:
    """ return all values for given field name and user """
    return HealthDiary.objects.filter(user=user).values(field_name)


def get_fields_usable_for_calculations() -> models:
    """ get field which can be use for calculations """
    usable_fields = []
    all_fields = HealthDiary._meta.get_fields()
    approved_field_types = (models.FloatField, models.PositiveIntegerField,
                            models.SmallIntegerField, models.PositiveSmallIntegerField, models.TimeField)
    for field in all_fields:
        if isinstance(field, approved_field_types):
            usable_fields.append(field)
    return usable_fields

def map_slug_to_health_diary_field(slug: str) -> str:
    """ map verbose name of field to model field name and return it """

    approved_fields = get_fields_usable_for_calculations()
    for field in approved_fields:
        if slug in [field.name, field.verbose_name]: return field.name
    return None

def get_weekly_avg_stats(user: get_user_model) -> dict:
    """ return """

    week_ago_date = datetime.date.today() - datetime.timedelta(days=7)
    instances = list(get_health_diaries(user=user).filter(date__gte=week_ago_date))

    allowed_field_names = get_fields_allowed_for_calculations()
    fields_total_value = {}
    fields_total_counter = {}

    for field in allowed_field_names:
        values_for_field, counter = sum_up_fields_values(field, instances)
        fields_total_value.update({field.name: values_for_field})
        fields_total_counter.update({field.name: counter})

    return calculate_avarage_value(fields_total_value, fields_total_counter)


def sum_up_fields_values(field: str, instances: HealthDiary )-> dict:
    """ sum up all fields values """
    total_value = 0
    counter = 0
    for instance in instances:
        value = getattr(instance, field.name, None)
        if value:
            if type(field) == models.TimeField:
                total_value += convert_time_to_seconds(value)
            else:
                total_value += value
            counter += 1
        else:
            continue
    return total_value, counter


def convert_time_to_seconds(time: datetime) -> int:
    """ convert time value to int """
    return time.hour * 3600 + time.minute * 60 + time.second


def calculate_avarage_value(total_value: dict, counter: dict) -> dict:
    """ calculate avarage based on sum up value and counter """
    for field, value in total_value.items():
        if counter[field] == 0:
            continue
        total_value.update({field: value/counter[field]})
    return total_value

def get_fields_allowed_for_calculations() -> list[models]:
        """ return only that fields which are allwod for calculations  """
        allowed_fields_types = (models.FloatField, models.PositiveIntegerField, models.SmallIntegerField, models.PositiveSmallIntegerField, models.TimeField)
        ommited_fields = ['last_update']
        all_fields = HealthDiary._meta.get_fields()
        allowed_fields = []
        for field in all_fields:
            if isinstance(field, allowed_fields_types) and field.name not in ommited_fields:
                allowed_fields.append(field)
        return allowed_fields