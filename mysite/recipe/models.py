from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode
import uuid
import os
import shutil
from django.conf import settings


# def recipe_image_file_path(instance, filename):
#     ext = filename.split('.')[-1]
#     filename = f'{uuid.uuid4()}.{ext}'
#
#     return os.path.join('recipes/', instance.user.name, instance.slug,
#                         filename)


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
    # photo1 = models.ImageField(upload_to=recipe_image_file_path, blank=True,
    #                            verbose_name='Zdjęcie 1')
    # photo2 = models.ImageField(upload_to=recipe_image_file_path, blank=True,
    #                            verbose_name='Zdjęcie 2')
    # photo3 = models.ImageField(upload_to=recipe_image_file_path, blank=True,
    #                            verbose_name='Zdjęcie 3')

    tags = models.ManyToManyField('Tag')
    ingredients = models.ManyToManyField('Ingredient',
                                         through='recipe_ingredient',
                                         related_name='ingredients_quantity')

    description = models.TextField(max_length=3000, default='',
                                   verbose_name='Przygotowanie', blank=True)

    # orginal_photos = []
    #
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.orginal_photos = [self.photo1, self.photo2, self.photo3]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('recipe:recipe_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        if self.check_if_slug_exists(self.slug):
            self.slug = self.slug + "2"

        # new_photos = [self.photo1, self.photo2, self.photo3]
        #
        # for old, new in zip(self.orginal_photos, new_photos):
        #     if new != old and old != '':
        #         self.delete_photo_from_media_folder(False, old)

        super().save(*args, **kwargs)

    def check_if_slug_exists(self, slug):
        return Ingredient.objects.filter(user=self.user). \
            filter(slug=slug).count()

    # def delete(self, *args, **kwargs):
    #     self.delete_photo_from_media_folder(True, *args)
    #     super().delete(*args, **kwargs)

    # def delete_photo_from_media_folder(self, all=False, *args):
    #
    #     if not all:
    #         for item in args:
    #             item = str(item)
    #             path = str(settings.MEDIA_DIR) + "/" + item
    #             if os.path.exists(path):
    #                 os.remove(path)
    #             else:
    #                 print(f"No such filepath{path}")
    #     else:
    #         path = str(settings.MEDIA_DIR) + \
    #             "/recipes/" + self.user.name + "/" + self.slug
    #         if os.path.exists(path):
    #             print(path)
    #             shutil.rmtree(path)
    #         else:
    #             print(f"No such filepath {path}")

    class Meta:
        unique_together = ('user', 'slug')


class Ingredient(models.Model):

    name = models.CharField(max_length=255, blank=False, unique=False,
                            verbose_name='Nazwa')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,
                             null=False, related_name='user')

    slug = models.SlugField(blank=False, unique=False)
    TYPE_CHOICE = [
        ('V', "wegańskie"),
        ('W', "wegetariańskie"),
        ('Z', "zwierzęce"),
    ]
    tag = models.ManyToManyField('Tag')

    def save(self, *args, **kwargs):
        """ two ingredient can have same slug eg 'sól' and 'sol' both
            have slug 'sol' """
        self.slug = slugify(unidecode(self.name))
        if self.check_if_slug_exists(self.slug) and not self.id:
            self.slug = self.slug + "2"

        super().save(*args, **kwargs)

    def check_if_slug_exists(self, slug):
        return Ingredient.objects.filter(user=self.user).filter(slug=slug).count()

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('user', 'name')


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

    quantity = models.CharField(max_length=25)

    def __str__(self):
        return self.recipe.name + '_' + self.ingredient.name
