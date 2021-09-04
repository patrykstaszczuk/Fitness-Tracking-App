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
            if obj._has_needed_informations():
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
            StravaApi.objects.create(user=self)
        url = settings.STRAVA_AUTH_URL
        res = self.strava._process_request(url=url, payload=payload,
                                                  type='POST')
        if not res:
            print(res.json())
            return False
        auth_data = {'expires_at': None, 'refresh_token': None, 'access_token': None}
        if all(attr in res for attr in auth_data.keys()):
            for data in auth_data.keys():
                setattr(self.strava, data, res[data])
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

    def _create_authorization_header(self):
        """ create authorization header including access token """
        return {'Authorization': f'Bearer {self.access_token}'}

    def _process_request(self, url, payload, type='GET'):
        """
        update last_request_epoc_time parameter and process strava response

        -------
        Returns (success):
        - response.json()
        Returns (failure):
        - None
        -------
        """

        self.last_request_epoc_time = time.time()
        self.save()
        response = self._send_request_to_strava(url, payload, type)
        if response:
            if response.status_code == 200:
                return response.json()
            else:
                print(response.json())
        return None

    def _send_request_to_strava(url, payload, type=None):
        """
        Send request to strava based on parameters

        -------
        Returns (success):
        - requests.response
        Returns (failure):
        - None
        -------

        """
        if type == 'GET':
            return requests.get(url, headers=payload)
        elif type == 'POST':
            return requests.post(url, payload)
        return None

    def _has_needed_informations(self):
        """
        check whether StravaApi instance has information needed
        for request
        """
        return all([self.access_token, self.refresh_token, self.expires_at])

    def _is_token_valid(self):
        """ check if token is still valid based on expiration time """
        return self.expires_at > time.time()

    def get_new_strava_access_token(self):
        """ request and save new accees token based on refresh_token parameter

        -------
        Returns (success):
        - True
        Returns (failure):
        - False
        -------
        """
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
        res = self._process_request(settings.STRAVA_AUTH_URL, payload, 'POST')

        if res:
            try:
                self.access_token = res['access_token']
                self.refresh_token = res['refresh_token']
                self.expires_at = res['expires_at']
                self.save()
                return True
            except KeyError:
                pass
        return False

    def get_strava_activities(self, date=datetime.date.today()):
        """ get strava activities for given date

        -------
        Returns (success):
        - list: list of activities
        Returns (failure):
        - None
        -------
        """

        one_day_in_seconds = 86400
        after_epoch_timestamp = int(time.mktime(time.strptime(date.strftime('%Y-%m-%d'),
                                    '%Y-%m-%d')))
        before_epoch_timestamp = after_epoch_timestamp + one_day_in_seconds
        params = [
            f'after={after_epoch_timestamp}',
            f'before={before_epoch_timestamp}',
        ]
        url = self._prepare_strava_request_url(id=None, params=params)
        header = self._create_authorization_header()

        if self._can_request_be_send():
            return self._process_request(url, header, 'GET')
        return None

    def get_strava_activity(self, id=None):
        """ get detailed information about strava activity
        -------
        Returns (success):
        - dict: activity details
        Returns (failure):
        - None
        -------
        """
        if id:
            url = self._prepare_strava_request_url(id=id)
            header = self._create_authorization_header()
            if self._can_request_be_send():
                return self._process_request(url, header, 'GET')
        return None

    def process_and_save_strava_activities(self, raw_activities):
        """ convert raw activities into StravaActivity objects
        -------
        Returns (success):
        - list: list of objects
        Returns (failure):
        - None
        -------
        """
        if raw_activities and isinstance(raw_activities, list):
            activity_objects = []
            for activity in raw_activities:
                strava_id = activity.get('id', None)
                if not strava_id:
                    continue
                url = self._prepare_strava_request_url(id=strava_id)
                header = self._create_authorization_header()
                raw_activity_details = self._process_request(url, header, 'GET')
                if raw_activity_details:
                    defaults = self._get_activity_details(raw_activity_details)
                    obj, created = StravaActivity.objects.update_or_create(
                        strava_id=strava_id, user=self.user, **defaults)
                    activity_objects.append(obj)
            return activity_objects
        return None

    def _get_activity_details(self, activity_details):
        """ get important properties, if not exsists pass it
        -------
        Returns :
        - dict: properties of activity
        -------
        """
        defaults = {}
        try:
            defaults['name'] = activity_details['name']
            defaults['calories'] = activity_details['calories']
            date_without_tz = activity_details['start_date_local'][:-1]
            defaults['date'] = date_without_tz
        except KeyError:
            pass
        return defaults

    def _can_request_be_send(self):
        """ check if request can be send based on actual information
        in database """
        return (self._is_token_valid() or self._has_needed_informations()
                and self.get_new_strava_access_token())

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
        """ get last_request_epoc_time """
        return self.last_request_epoc_time


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
