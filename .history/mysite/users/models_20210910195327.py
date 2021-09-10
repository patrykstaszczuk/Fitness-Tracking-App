from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
                                PermissionsMixin
from django.urls import reverse
from django.contrib.auth import get_user_model
from health.models import HealthDiary
import datetime
import requests
import os
import time
import json
from django.core.exceptions import ValidationError
from mysite import settings
from rest_framework import status


class MyManager(BaseUserManager):
    """ custom manager providing create_user and create_superuser
    custom methods """

    def create_user(self, email, password=None, **extra_fields):
        """ Create, save and return new user, aditionally create related Group
        and StravaApi object """

        if not email:
            raise ValueError('Email must be provided!')
        user = self.model(
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self.db)

        Group.objects.create(founder=user, name=f'{user.name} group')
        StravaApi.objects.create(user=user)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """ create standard user with additional parameters """

        user = self.create_user(
            email=email,
            password=password,
            **extra_fields
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self.db)
        return user


class MyUser(AbstractBaseUser, PermissionsMixin):
    """ Custom user model """
    email = models.EmailField(unique=True, max_length=255,
                              error_messages={'unique': 'Podany adres email jest zajęty'})
    name = models.CharField(blank=False, max_length=255, unique=True,
                            error_messages={'unique': 'Podana nazwa jest zajęta'})
    password = models.CharField(blank=False, max_length=255)

    MALE = 'Male'
    FEMALE = 'Female'

    GENDER_CHOICE = (
        (MALE, 'M'),
        (FEMALE, 'F'),
    )

    gender = models.CharField(max_length=6, choices=GENDER_CHOICE, null=False,
                              blank=False, default='M')
    age = models.IntegerField()
    height = models.PositiveSmallIntegerField()
    weight = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'gender', 'age']

    objects = MyManager()

    def get_bmi(self):
        """ calcualte and return BMI
        -------
        Returns:
        - bmi: float
        -------
        """
        return round(self.weight/(self.height/100)**2, 1)

    def get_memberships(self):
        """ get user groups membership
        -------
        Returns (exist):
        - queryset: Group object
        Returns (non-exists):
        - None
        -------
        """
        return self.membership.all()

    def get_weekly_avg_stats(self):
        """ calculate and return weekly avarage statistics
        -------
        Returns (exist):
        - queryset: Group object
        Returns (non-exists):
        - empty dict
        -------
        """
        week_ago_date = datetime.date.today() - datetime.timedelta(days=7)
        queryset = HealthDiary.objects.filter(user=self.id) \
            .filter(date__gte=week_ago_date)

        fields_total_value_and_counter = {}

        for instance in queryset:
            all_instance_fields = instance._meta.get_fields()
            allowed_fields = self._get_allowed_fields(all_instance_fields)
            for field in allowed_fields:
                field_value = getattr(instance, field.name, None)
                if field_value is not None:
                    if fields_total_value_and_counter.get(field.name, None):
                        current_value = fields_total_value_and_counter[field.name]['value']
                        current_counter = fields_total_value_and_counter[field.name]['counter']
                    else:
                        current_value = 0
                        current_counter = 0
                    fields_total_value_and_counter.update({field.name:
                                                          {'value': current_value + field_value,
                                                           'counter': current_counter + 1}})

        return self._calculate_avg_values(fields_total_value_and_counter)

    def _get_allowed_fields(self, all_fields):
        """
        return only that fields which are allwod for calculations

        Returns:
        - model fields: type

        """
        allowed_fields_types = (models.FloatField, models.PositiveIntegerField,
                                models.SmallIntegerField)
        ommited_fields = ['last_update']
        allowed_fields = []
        for field in all_fields:
            if isinstance(field, allowed_fields_types) and field.name not in ommited_fields:
                allowed_fields.append(field)
        return allowed_fields

    def _calculate_avg_values(self, field_values_and_counter):
        """
        caclulate avarage value for given fields

        Return:
        - field, avg_value pair: dict
        """
        for key, value in field_values_and_counter.items():
            value = value['value']/value['counter']
            field_values_and_counter.update({key: value})
        return field_values_and_counter

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        if self.is_active and self.is_superuser:
            return True

    def get_absolute_url(self):
        return reverse('users:profile')


class StravaApi(models.Model):
    """
    Store strava tokens related informations and provide methods
    for requesting strava API
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                null=False, related_name='strava')
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    expires_at = models.PositiveIntegerField(null=True, default=0)
    last_request_epoc_time = models.FloatField(default=0, null=False)

    def __str__(self):
        return str(self.user) + str(self.expires_at)


class StravaActivity(models.Model):
    """ store activities downloaded from Strava API """

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, null=False,
                             related_name='stava_activity')
    date = models.DateTimeField(default=datetime.datetime.now)
    strava_id = models.PositiveBigIntegerField(unique=True, null=False)
    name = models.CharField(max_length=255, null=True)
    calories = models.PositiveIntegerField(null=True)

    def __str__(self):
        return self.name


class GroupManager(models.Manager):
    """ implementing custom create method """

    def create(self, *args, **kwargs):
        """ set the name of group and add founder to members """
        instance = super().create(*args, **kwargs)
        instance.name = instance.founder.name + 's group'
        instance.members.add(instance.founder)
        instance.save()
        return instance


class Group(models.Model):
    """ store group informations """
    name = models.CharField(max_length=100, blank=False)
    founder = models.OneToOneField(get_user_model(), on_delete=models.CASCADE,
                                unique=True, null=False, blank=False,
                                related_name='own_group')
    members = models.ManyToManyField('MyUser', related_name='membership')
    pending_membership = models.ManyToManyField('MyUser', related_name=
                                                'pending_membership')
    objects = GroupManager()

    def __str__(self):
        return self.founder.name + 's group'
