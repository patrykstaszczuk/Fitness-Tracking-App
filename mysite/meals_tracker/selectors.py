import datetime
from typing import Iterable

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.auth import get_user_model

from meals_tracker.models import Meal, MealCategory, RecipePortion, IngredientAmount


def meal_list(user: get_user_model, date: datetime = None):
    if not date:
        date = datetime.datetime.today()
    else:
        meal_validate_date(date)
    return Meal.objects.filter(user=user, date=date)


def meal_get(user: get_user_model, id: int) -> Meal:
    try:
        id = int(id)
    except ValueError:
        raise ValidationError(f'Incorrect id: {id} for meal ')
    try:
        return Meal.objects.get(user=user, id=id)
    except Meal.DoesNotExist:
        raise ObjectDoesNotExist(f'Meal with id {id} does not exists!')


def meal_get_recipes(user: get_user_model, id: int) -> Iterable[RecipePortion]:
    meal = meal_get(user, id)
    return meal.recipe_portion.all().prefetch_related('recipe')


def meal_get_recipes_detail(meal: Meal, id: int) -> RecipePortion:

    try:
        return RecipePortion.objects.get(id=id, meal=meal)
    except RecipePortion.DoesNotExist:
        raise ObjectDoesNotExist(
            f'No recipe with id {id} under meal with id {meal.id}')


def meal_get_ingredients_detail(meal: Meal, id: int) -> IngredientAmount:
    try:
        return IngredientAmount.objects.get(id=id, meal=meal)
    except IngredientAmount.DoesNotExist:
        raise ObjectDoesNotExist(
            f'No ingredient with id {id} under meal with id {meal.id}')


def meal_get_ingredients(user: get_user_model, id: int) -> Iterable[IngredientAmount]:
    meal = meal_get(user, id)
    return meal.ingredientamount_set.all().prefetch_related('ingredient', 'unit')


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
    return Meal.objects.filter(user=user).values('date').distinct()


def meal_category_list():
    """ return all available categories """
    return MealCategory.objects.all()
