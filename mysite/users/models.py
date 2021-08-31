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

    def create_user(self, email, password=None, **extra_fields):
        """ Create and saves a new user """
        if not email:
            raise ValueError('Email must be provided!')
        user = self.model(
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self.db)

        Group.objects.create(founder=user)

        return user

    def create_superuser(self, email, password=None, **extra_fields):

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
        """ return calculated bmi """
        return round(self.weight/(self.height/100)**2, 1)

    def get_memberships(self):
        return self.membership.all()

    # def leave_group(self, group_id):
    #     """ leave group """
    #     try:
    #         group = Group.objects.get(id=group_id, members=self)
    #         if group.founder == self:
    #             raise Group.DoesNotExist
    #         self.membership.remove(group)
    #     except Group.DoesNotExist as error:
    #         raise error

    def get_weekly_avg_stats(self):
        """ get weekly avg weight """
        week_ago = datetime.date.today() - datetime.timedelta(days=7)
        queryset = HealthDiary.objects.filter(user=self.id) \
            .filter(date__gte=week_ago)

        fields_avg_values = {}
        if queryset:
            fields_value_counter = {}
            for instance in queryset:
                for field in instance._meta.get_fields():
                    allowed_fields = (models.FloatField,
                                      models.PositiveIntegerField,
                                      models.SmallIntegerField)
                    if isinstance(field, allowed_fields):
                        current_value = fields_avg_values.get(field.name, 0)
                        current_counter = fields_value_counter.get(field.name,
                                                                   0)
                        getattr_value = getattr(instance, field.name, None)
                        if getattr_value is not None:
                            fields_avg_values.update(
                                    {field.name: current_value +
                                     getattr_value})
                            fields_value_counter.update({field.name:
                                                        current_counter + 1})

            for key, value in fields_avg_values.items():
                value = value/fields_value_counter[key]
                fields_avg_values.update({key: value})

        return fields_avg_values

    def get_environ_variables(self):
        """ get client id and cliend secret needed for user app
        authorization """
        return os.environ['STRAVA_CLIENT_ID'], os.environ['STRAVA_CLIENT_SECRET']

    def is_auth_to_strava(self):
        """ check if user has associated strava info """
        try:
            obj = StravaTokens.objects.get(user=self.id)
            if obj.valid:
                return True
        except StravaTokens.DoesNotExist:
            StravaTokens.objects.create(user=self, valid=False)
        return False

    def authorize_to_strava(self, code):
        """ authorize to strava with provided code and save info in db """

        try:
            client_id, client_secret = self.get_environ_variables()
        except KeyError:
            return False
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        res = self.strava.authorize(payload)
        if res.status_code != 200:
            print(res.json())
            return False
        auth_data = {'expires_at': None, 'refresh_token': None, 'access_token': None}
        if all(attr in res.json() for attr in auth_data.keys()):
            for data in auth_data.keys():
                setattr(self.strava, data, res.json()[data])
            self.strava.save()
            return True
        return False

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        if self.is_active and self.is_superuser:
            return True

    def get_absolute_url(self):
        return reverse('users:profile')


class StravaTokens(models.Model):
    """ model for storing strava tokens """

    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                null=False, related_name='strava')
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    expires_at = models.PositiveIntegerField(null=True)
    last_update = models.FloatField(default=0, null=False)
    valid = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user) + str(self.expires_at)

    def authorize(self, payload):
        """ send authorization request to strava """
        self.last_update = time.time()
        return requests.post(settings.STRAVA_AUTH_URL, payload)

    def get_last_update_time(self):
        return self.last_update

    def get_burned_calories_for_given_day(self, date):
        """ return burned calories from strava activities """
        pass
    # def check_expiration_date(self):
    #     """ check if expiration date < today """
    #     today = datetime.date.today()
    #     if


class GroupManager(models.Manager):
    """ set the name of group, and add founder to members """

    def create(self, *args, **kwargs):
        instance = super().create(*args, **kwargs)
        instance.name = instance.founder.name + 's group'
        instance.members.add(instance.founder)
        instance.save()
        return instance


class Group(models.Model):

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
