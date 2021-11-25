from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.validators import MinValueValidator as MinValue
from django.utils.text import slugify
from unidecode import unidecode
from django.core.exceptions import ValidationError
import uuid
import os
import shutil
from django.conf import settings

import requests
from rest_framework import status


def generate_image_file_path(recipe_instance, filename: str):
    """ generate file path for new recipe image """
    extention = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{extention}'
    return os.path.join('recipes/', recipe_instance.user.name,
                        recipe_instance.slug, filename)


class Dish(models.Model):
    """ abstract class for any kind of dish. Provided common attributes and methods """

    name = models.CharField(max_length=255, blank=False, unique=False,
                            verbose_name='Name')
    slug = models.SlugField(blank=False, unique=False)
    calories = models.FloatField(verbose_name='Calories', blank=True, null=True,
                                 default=0, validators=[MinValue(0)])
    proteins = models.FloatField(blank=True, null=True, default=0,
                                 validators=[MinValue(0)])
    carbohydrates = models.FloatField(blank=True, null=True, default=0,
                                      validators=[MinValue(0)])
    fats = models.FloatField(blank=True, null=True,
                             default=0, validators=[MinValue(0)])
    tags = models.ManyToManyField('Tag')

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name

    def _check_if_name_exists(self, name: str) -> int:
        """ check if and how many recipes with provided name exists """
        return self.__class__.objects.filter(user=self.user) \
            .filter(name=name).exclude(id=self.id).count()


class Recipe(Dish):

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             null=False, related_name='recipe')
    portions = models.PositiveSmallIntegerField(
        verbose_name='Porcje', blank=False, null=False,
        default=1, validators=[MinValue(1)])
    prepare_time = models.PositiveSmallIntegerField(
        verbose_name='Czas przygotowania', blank=True, null=True, default=0,
        validators=[MinValue(0)])

    photo1 = models.ImageField(upload_to=generate_image_file_path, blank=True,
                               verbose_name='Zdjęcie 1', null=True)
    photo2 = models.ImageField(upload_to=generate_image_file_path, blank=True,
                               verbose_name='Zdjęcie 2', null=True)
    photo3 = models.ImageField(upload_to=generate_image_file_path, blank=True,
                               verbose_name='Zdjęcie 3', null=True)
    ingredients = models.ManyToManyField('Ingredient',
                                         through='recipe_ingredient',
                                         related_name='ingredients_quantity')

    description = models.TextField(max_length=3000, default='',
                                   verbose_name='Przygotowanie', blank=True)

    orginal_photos = []

    class Meta:
        unique_together = ('user', 'name')

    def save(self, *args, **kwargs) -> None:
        """ save object with appropriate slug """
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.id:
            new_photos = [self.photo1, self.photo2, self.photo3]
            for old, new in zip(self.orginal_photos, new_photos):
                if new != old and old not in ('', None):
                    try:
                        path = old.path
                        if os.path.exists(path):
                            os.remove(path)
                    except AttributeError:
                        pass

    # def get_ingredients(self):
    #     """ return all ingredients with recipe_ingredents prefetched,
    #      needed for RecipeDetailOutputSerializer """
    #     return self.ingredients.all().prefetch_related('recipe_ingredient_set')

    def get_absolute_url(self) -> str:
        return reverse('recipe:recipe_detail', kwargs={'slug': self.slug})

    def __init__(self, *args, **kwargs):
        """ save curently used photos in list for latter comparsion """
        super().__init__(*args, **kwargs)
        self.orginal_photos = [self.photo1, self.photo2, self.photo3]


class Ingredient(Dish):

    SOLID = 'S'
    LIQUID = 'L'
    TYPE_CHOICE = [
        (SOLID, 'solid'),
        (LIQUID, 'liquid')
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             null=False, related_name='user')
    slug = models.SlugField(blank=False, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICE, null=True)
    units = models.ManyToManyField('Unit', through='ingredient_unit',)
    fiber = models.FloatField(null=True, validators=[MinValue(0)])
    sodium = models.FloatField(null=True, validators=[MinValue(0)])
    potassium = models.FloatField(null=True, validators=[MinValue(0)])
    calcium = models.FloatField(null=True, validators=[MinValue(0)])
    iron = models.FloatField(null=True, validators=[MinValue(0)])
    magnesium = models.FloatField(null=True, validators=[MinValue(0)])
    selenium = models.FloatField(null=True, validators=[MinValue(0)])
    zinc = models.FloatField(null=True, validators=[MinValue(0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'],
                                    name='unique_user_name')
        ]


class ReadyMeals(Ingredient):
    """ proxy model for ready meals """

    class Meta:
        proxy = True

    def __str__(self):
        return self.name


class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             null=False)
    name = models.CharField(max_length=25)

    slug = models.SlugField(blank=False, unique=False, null=False)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('user', 'name')


class Recipe_Ingredient(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, null=False,
                               related_name='ingredients_quantity')
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE,
                                   null=False)
    amount = models.FloatField(null=True)
    unit = models.ForeignKey('Unit', null=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.recipe.name + '_' + self.ingredient.name


class Unit(models.Model):

    name = models.CharField(max_length=10)
    short_name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Ingredient_Unit(models.Model):
    """ Intermediate model for ingredient and unit """

    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE,
                                   null=False)
    unit = models.ForeignKey('Unit', on_delete=models.PROTECT, null=False)
    grams_in_one_unit = models.PositiveSmallIntegerField(null=False,
                                                         default=100)

    def __str__(self):
        return self.ingredient.name + ' ' + self.unit.name + \
            '(' + str(self.grams_in_one_unit) + ')'
