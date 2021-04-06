from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
                                PermissionsMixin
from django.urls import reverse


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
    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(blank=False, max_length=255)
    password = models.CharField(blank=False, max_length=255)

    MALE = 'Male'
    WOMAN = 'WOMAN'

    SEX_CHOICE = (
        (MALE, 'Mężczyzna'),
        (WOMAN, 'Kobieta'),
    )

    sex = models.CharField(max_length=5, choices=SEX_CHOICE, default=MALE)
    age = models.IntegerField()
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'sex', 'age']

    objects = MyManager()

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        if self.is_active and self.is_superuser:
            return True

    def get_absolute_url(self):
        return reverse('users:profile')
