from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.validators import MinValueValidator as MinValue
from django.utils.text import slugify
from unidecode import unidecode
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
import uuid
import os
import shutil
from django.conf import settings

import requests
from rest_framework import status


def recipe_image_file_path(instance, filename):
    """ generate file path for new recipe image """
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('recipes/', instance.user.name, instance.slug,
                        filename)

# class CustomRecipeManager(models.Manager):
#     """ override save method for automate calories calculation """
#
#     def save(self):
#         instance = super().save()
#         print(instance)


class Recipe(models.Model):

    name = models.CharField(max_length=255, blank=False, verbose_name='Nazwa')
    user = models.ForeignKey(get_user_model(),
                             on_delete=models.CASCADE,
                             null=False, related_name='recipe')
    calories = models.IntegerField(verbose_name='Kalorie', blank=True,
                                   null=True, default=0)
    portions = models.IntegerField(verbose_name='Porcje', blank=True,
                                   null=True)
    prepare_time = models.IntegerField(verbose_name='Czas przygotowania',
                                       blank=True, null=True, default=0)
    slug = models.SlugField(blank=False)

    photo1 = models.ImageField(upload_to=recipe_image_file_path, blank=True,
                               verbose_name='Zdjęcie 1', null=True)
    photo2 = models.ImageField(upload_to=recipe_image_file_path, blank=True,
                               verbose_name='Zdjęcie 2', null=True)
    photo3 = models.ImageField(upload_to=recipe_image_file_path, blank=True,
                               verbose_name='Zdjęcie 3', null=True)

    tags = models.ManyToManyField('Tag')
    ingredients = models.ManyToManyField('Ingredient',
                                         through='recipe_ingredient',
                                         related_name='ingredients_quantity')

    description = models.TextField(max_length=3000, default='',
                                   verbose_name='Przygotowanie', blank=True)

    orginal_photos = []

    # objects = CustomRecipeManager()

    class Meta:
        unique_together = ('user', 'slug')

    def __init__(self, *args, **kwargs):
        """ save curently used photos in list, to be used later in comparsion,
        set self.portions to 1 if is None or 0 """

        super().__init__(*args, **kwargs)
        self.orginal_photos = [self.photo1, self.photo2, self.photo3]

        if self.portions is None or self.portions == 0:
            self.portions = 1

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ check if there is existing slug for different recipe """
        self.slug = slugify(unidecode(self.name))
        if self.check_if_slug_exists(self.slug) and not self.id:
            self.slug = self.slug + "2"

        if self.id:
            """ check if images change after upload """
            new_photos = [self.photo1, self.photo2, self.photo3]
            for old, new in zip(self.orginal_photos, new_photos):
                if new != old and old not in ('', None):
                    path = old.path
                    if os.path.exists(path):
                        os.remove(path)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('recipe:recipe_detail', kwargs={'slug': self.slug})

    def check_if_slug_exists(self, slug):
        """ check if slug already exists in db """

        return Recipe.objects.filter(user=self.user). \
            filter(slug=slug).count()

    def delete(self, *args, **kwargs):
        """ delete all photos belong to specific recipe """

        path = str(settings.MEDIA_ROOT) + \
            "/recipes/" + self.user.name + "/" + self.slug
        if os.path.exists(path):
            shutil.rmtree(path)
        else:
            print(f"No such filepath {path}")
        super().delete(*args, **kwargs)

    def get_calories(self, number_of_portions):
        """ return calories based on portions """
        if self.calories is None:
            self.calories = 0
        if number_of_portions == 0:
            number_of_portions = 1
        return (self.calories/self.portions) * number_of_portions


class Ingredient(models.Model):

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
    name = models.CharField(max_length=255, blank=False, unique=False,
                            verbose_name='Nazwa')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,
                             null=False, related_name='user')

    slug = models.SlugField(blank=False, unique=False)
    tags = models.ManyToManyField('Tag')
    type = models.CharField(max_length=10, choices=TYPE_CHOICE, null=True)
    _usage_counter = models.PositiveIntegerField(default=0, null=False)
    units = models.ManyToManyField('Unit', through='ingredient_unit',)
    calories = models.FloatField(null=True, validators=[MinValue(1, "Value \
                        must be greater then 0!")])
    carbohydrates = models.FloatField(null=True, validators=[MinValue(0)])
    proteins = models.FloatField(null=True, validators=[MinValue(0)])
    fats = models.FloatField(null=True, validators=[MinValue(0)])
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

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ two ingredient can have same slug eg 'sól' and 'sol' both
            have slug 'sol' """
        self.slug = slugify(unidecode(self.name))
        if self.check_if_slug_exists(self.slug) and not self.id:
            self.slug = self.slug + "2"
        super().save(*args, **kwargs)

        gram_unit_instance = Unit.objects.get(name='gram')
        self.units.add(gram_unit_instance,
                      through_defaults={'grams_in_one_unit': 100})

    @property
    def usage_counter(self):
        return self._usage_counter

    @usage_counter.setter
    def usage_counter(self, value):
        self._usage_counter = self._usage_counter + value

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

    def check_if_slug_exists(self, slug):
        return Ingredient.objects.filter(user=self.user).filter(slug=slug).count()

    @property
    def get_calories(self):
        return self.calories

    @property
    def get_unit(self):
        return self.unit

    def get_unit_weight(self, unit, amount):
        """ return the unit and amount in grams/mililiters """
        try:
            obj = Ingredient_Unit.objects.get(
                ingredient=self.id, unit=unit)
        except Ingredient_Unit.DoesNotExist:
            raise ValidationError(f"{unit} - {self.name} no such mapping")
        return obj.grams_in_one_unit * amount


class Tag(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,
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
    unit = models.ForeignKey('Unit', null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.recipe.name + '_' + self.ingredient.name

@receiver(m2m_changed, sender=Recipe_Ingredient)
def _count_calories_based_on_ingredients(sender, instance, action, **kwargs):
    """ sum up calories from all recipe ingredients """
    if action == 'post_add':
        instance.calories = 0
        for ingredient in instance.ingredients.all():
            obj = sender.objects.get(recipe=instance, ingredient=ingredient)
            if ingredient.calories is not None:
                if obj.amount or obj.unit is not None:
                    if obj.unit.name != 'gram':
                        raw_weigth = ingredient.get_unit_weight(obj.unit,
                                                                obj.amount)
                    else:
                        raw_weigth = obj.amount
                    instance.calories += (raw_weigth/100)*ingredient.calories
        instance.save()


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
        return self.ingredient.name + ' ' + self.unit.name + '(' + str(self.grams_in_one_unit) + ')'
