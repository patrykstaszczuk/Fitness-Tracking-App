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
        StravaApi.objects.create(user=user)

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
            obj = StravaApi.objects.get(user=self.id)
            if obj.has_needed_informations():
                return True
        except StravaApi.DoesNotExist:
            StravaApi.objects.create(user=self, valid=False)
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
        if not hasattr(self, 'strava'):
            StravaApi.objects.create(user=self, valid=False)
        res = self.strava.authorize(payload)
        if res.status_code != 200:
            print(res.json())
            return False
        auth_data = {'expires_at': None, 'refresh_token': None, 'access_token': None}
        if all(attr in res.json() for attr in auth_data.keys()):
            for data in auth_data.keys():
                setattr(self.strava, data, res.json()[data])
            self.strava.valid = True
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


class StravaApi(models.Model):
    """ model for storing strava tokens """

    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                null=False, related_name='strava')
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    expires_at = models.PositiveIntegerField(null=True, default=0)
    last_request_epoc_time = models.FloatField(default=0, null=False)

    def __str__(self):
        return str(self.user) + str(self.expires_at)

    def create_strava_header_token(self):
        """ create proper hedader with strava token """
        return f'Authorization: Bearer [[{self.access_token}]]'

    def authorize(self, payload):
        """ send authorization request to strava """
        self.last_request_epoc_time = time.time()
        return self._send_request_to_strava(url=settings.STRAVA_AUTH_URL,
                                            type='POST',
                                            payload=payload)

    def _send_request_to_strava(self, url, payload, type='GET'):
        """ send request to strava API """
        if type == 'GET':
            pass
        elif type == 'POST':
            return requests.post(url, payload)
        else:
            return False

    def has_needed_informations(self):
        """ check if information are in db """
        if not all([self.access_token, self.refresh_token, self.expires_at]):
            return False
        return True

    def is_token_valid(self):
        """ check is valid time for token expired """
        return self.expires_at > time.time()

    def get_new_strava_access_token(self):
        """ request new access token """
        try:
            client_id, client_secret = self.user.get_environ_variables()
        except KeyError:
            return False

        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        res = self._send_request_to_strava(settings.STRAVA_AUTH_URL,
                                           payload,
                                           'POST')
        if res.status_code == 200:
            self._save_new_strava_auth_information(res)
            return True
        print(res.json())
        return False

    def _save_new_strava_auth_information(self, res):
        """ save new access token, refresh_token and expires_at in db """
        self.access_token = res.json()['access_token']
        self.refresh_token = res.json()['refresh_token']
        self.expires_at = res.json()['expires_at']
        self.save()

    def get_strava_activities(self, date=datetime.date.today()):
        """ get strava activities list for given date or activity
         detail if id probided """
        params = [
            f'before{date}',
            'after=',
            'page=',
            'per_page='
        ]
        url = self._prepare_strava_request_url(id=None, params=params)
        header = self.create_strava_header_token()

        if self.can_request_be_send():
            return self._send_request_to_strava(url, header, 'GET').json()
        return None

    def get_strava_activity(self, id=None):
        """ get detailed information about strava activity """
        if id:
            url = self._prepare_strava_request_url(id=id)
            header = self.create_strava_header_token()
            if self.can_request_be_send():
                return self._send_request_to_strava(url, header, 'GET').json()
        return None

    def process_and_save_strava_activities(self, raw_activities):
        """ convert raw strava API response with activities to
        StravaActivity objects"""
        if raw_activities and isinstance(raw_activities, list):
            defaults = {}
            activities = []
            for activity in raw_activities:
                strava_id = activity.get('strava_id', None)
                if not strava_id:
                    continue
                try:
                    strava_id = activity['strava_id']
                    defaults['name'] = activity['name']
                    defaults['calories'] = activity['calories']
                    defaults['date'] = activity['start_date_local']
                except KeyError:
                    pass
                obj, created = StravaActivity.objects.update_or_create(
                    strava_id=strava_id, user=self.user, **defaults)
                activities.append(obj)
            return activities
        return None

    def can_request_be_send(self):
        """ check if request can be send with given information """
        return (self.is_token_valid() or self.has_needed_informations() and self.get_new_strava_access_token())

    def _prepare_strava_request_url(self, id=None, params=None):
        """ prepare strava url for request """
        if id:
            url = f'https://www.strava.com/api/v3/activities/{id}'
        else:
            url = 'https://www.strava.com/api/v3/athlete/activities?'
            for param in params:
                url += param + '&'
        return url

    def get_last_request_epoc_time(self):
        return self.last_request_epoc_time

    def get_burned_calories_for_given_day(self, date):
        """ return burned calories from strava activities """
        pass


class StravaActivity(models.Model):
    """ model for strava activities """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, null=False,
                             related_name='stava_activity')
    date = models.DateTimeField(default=datetime.datetime.now)
    strava_id = models.PositiveIntegerField(null=False)
    name = models.CharField(max_length=255, null=True)
    calories = models.PositiveIntegerField(null=True)

    def __str__(self):
        return self.name


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
