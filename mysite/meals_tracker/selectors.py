from meals_tracker.models import Meal, MealCategory
import datetime
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.auth import get_user_model


def meal_list(user: get_user_model, date: datetime = None):
    """ retrieve meals for given user and date """
    if not date:
        today = datetime.datetime.today()
        return Meal.objects.filter(user=user, date=today)
    else:
        meal_validate_date(date)
        return Meal.objects.filter(user=user, date=date)


def meal_get(user: get_user_model, id: int) -> Meal:
    """ return meal based on user and id """
    try:
        return Meal.objects.get(user=user, id=id)
    except Meal.DoesNotExist:
        raise ObjectDoesNotExist(f'Meal with id {id} does not exists!')


def meal_validate_date(date: datetime):
    """ validate if date is not exceed today """
    if isinstance(date, str):
        try:
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError(
                'Invalid date format, It must be in YYYY-MM-DD format')
    if date > datetime.date.today():
        raise ValidationError(
            f'You cannot retrieve meals list for the future!')


def meal_get_available_dates(user):
    """ return all dates where at least one meal was created """
    return Meal.objects.filter(user=user).values('date')


def meal_category_list():
    """ return all available categories """
    return MealCategory.objects.all()
