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

def generate_image_file_path(recipe_instance, filename: str):
    """ generate file path for new recipe image """
    extention = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{extention}'
    return os.path.join('recipes/', recipe_instance.user.name,
                        recipe_instance.slug, filename)


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
        unique_together = ('user', 'slug')


    def save(self, *args, **kwargs) -> None:
        """ save object with appropriate slug """

        self.slug = slugify(unidecode(self.name))
        number_of_recipes_with_same_name = self._check_if_name_exists(
            self.name)
        if number_of_recipes_with_same_name > 0:
            self.slug = self.slug + str(number_of_recipes_with_same_name + 1)
        if self.id:
            new_photos = [self.photo1, self.photo2, self.photo3]
            self._delete_old_photos(new_photos, self.orginal_photos)
        super().save(*args, **kwargs)


    def _delete_old_photos(self, new_photos: list, old_photos: list) -> None:
        """ check if images change after upload and delete old from folder
        if so """
        for old, new in zip(old_photos, new_photos):
            if new != old and old not in ('', None):
                try:
                    path = old.path
                    if os.path.exists(path):
                        os.remove(path)
                except AttributeError:
                    pass

    def _recalculate_nutritions_values(self) -> None:
        """ recalculating recipe nutritions values based on ingredients """

        nutritional_fields = ['proteins', 'carbohydrates', 'fats', 'calories']
        self.proteins = 0
        self.carbohydrates = 0
        self.fats = 0
        self.calories = 0
        for ingredient in self.ingredients.all():
            obj = Recipe_Ingredient.objects.get(recipe=self,
                                                ingredient=ingredient)
            unit = obj.unit
            amount = obj.amount
            if not all([unit, amount]):
                continue
            for field in nutritional_fields:
                current_recipe_field_value = getattr(self, field)
                ingredient_field_value = getattr(ingredient, field)
                if ingredient_field_value is None:
                    ingredient_field_value = 0
                grams = ingredient.convert_unit_to_grams(unit, amount)
                setattr(self, field, round((current_recipe_field_value
                                            + (grams/100)*ingredient_field_value), 2))
        kwargs = {'force_insert': False}
        super().save(**kwargs, update_fields=['proteins', 'carbohydrates',
                                                     'fats', 'calories'])

    def get_absolute_url(self) -> str:
        return reverse('recipe:recipe_detail', kwargs={'slug': self.slug})

    def delete(self, *args, **kwargs) -> None:
        """ delete all photo folder related to specific user and
        recipe """
        path = str(settings.MEDIA_ROOT) + \
            "/recipes/" + self.user.name + "/" + self.slug
        if os.path.exists(path):
            shutil.rmtree(path)
        super().delete(*args, **kwargs)

    def get_recalculated_calories(self, number_of_portions: int) -> int:
        """ return calories based on portions """
        return (self.calories/self.portions) * number_of_portions

    def __init__(self, *args, **kwargs):
        """ save curently used photos in list for latter comparsion """
        super().__init__(*args, **kwargs)
        self.orginal_photos = [self.photo1, self.photo2, self.photo3]


class Ingredient(Dish):

    GRAM = 'G'
    MILI = 'ML'
    UNIT_CHOICE = [
        (GRAM, 'g'),
        (MILI, 'ml'),
    ]

    SOLID = 'S'
    LIQUID = 'L'
    TYPE_CHOICE = [
        (SOLID, 'solid'),
        (LIQUID, 'liquid')
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             null=False, related_name='user')

    type = models.CharField(max_length=10, choices=TYPE_CHOICE, null=True)
    _usage_counter = models.PositiveIntegerField(default=0, null=False)
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


    def save(self, *args, **kwargs):
        """
            - edit slug field if similar slug exists
            - add default unit for ingredient
        """
        self.slug = slugify(unidecode(self.name))
        number_of_ingredients_with_the_same_name = self._check_if_name_exists(
            self.name)
        if number_of_ingredients_with_the_same_name > 0:
            self.slug = self.slug + str(number_of_ingredients_with_the_same_name + 1)
        super().save(*args, **kwargs)


    def send_to_nozbe(self):
        """ send ingredient instance to nozbe """

        res = requests.post('https://api.nozbe.com:3000/task',
                            headers={'Authorization':
                                     os.environ['NOZBE_SECRET']},
                            data={'name': self.name, 'project_id':
                                  os.environ['NOZBE_PROJECT_ID'],
                                  'client_id': os.environ['NOZBE_CLIENT_ID']})
        if res.status_code == status.HTTP_200_OK:
            self.usage_counter += 1
            return True

    def _check_if_name_exists(self, slug):
        return Ingredient.objects.filter(user=self.user).filter(slug=slug).count()

    def get_default_calories(self):
        """ get calories on 100 gram """
        return self.calories

    @property
    def get_unit(self):
        return self.unit

    def convert_unit_to_grams(self, unit, amount):
        """ return the unit and amount in grams/mililiters defined for
        ingredient """

        if unit.name == 'gram':
            return amount
        try:
            obj = Ingredient_Unit.objects.get(
                ingredient=self.id, unit=unit)
        except Ingredient_Unit.DoesNotExist:
            raise ValidationError(f"{unit} - {self.name} no such mapping")
        return obj.grams_in_one_unit * amount

    def calculate_calories(self, unit, amount):
        """ calculate calories based on unit and amount """
        return (self.convert_unit_to_grams(unit, amount)/100) * \
            self.get_default_calories()


class ReadyMeals(Ingredient):
    """ proxy model for ready meals """

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        """ set default tag for ready meal or create that tag if not exists """

        if not self.id:
            super().save(*args, **kwargs)
            tag, created = Tag.objects.get_or_create(name='Ready Meal',
                                                     defaults={"user": self.user})
            self.tags.add(tag)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             null=False)
    name = models.CharField(max_length=25)

    slug = models.SlugField(blank=False, unique=False)

    def save(self, *args, **kwargs):
        """ two tags can have same slug eg 'sól' and 'sol' both
            have slug 'sol' """
        self.slug = slugify(unidecode(self.name))
        if self.check_if_slug_exists(self.slug) and not self.id:
            self.slug = self.slug + "2"

        super().save(*args, **kwargs)

    def check_if_slug_exists(self, slug):
        return Tag.objects.filter(user=self.user).filter(slug=slug).count()

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
