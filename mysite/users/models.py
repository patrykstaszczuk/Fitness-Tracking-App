from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
                                PermissionsMixin
from django.urls import reverse
import datetime
from mysite import settings


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

    gender = models.CharField(max_length=6, choices=GENDER_CHOICE, null=True,
                              blank=True, default='M')
    age = models.IntegerField(null=True)
    height = models.PositiveSmallIntegerField(null=True)
    weight = models.PositiveSmallIntegerField(null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'gender', 'age']

    objects = MyManager()

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
    founder = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   unique=True, null=False, blank=False,
                                   related_name='own_group')
    members = models.ManyToManyField('MyUser', related_name='membership')
    pending_membership = models.ManyToManyField(
        'MyUser', related_name='pending_membership')
    objects = GroupManager()

    def __str__(self):
        return self.founder.name + 's group'
