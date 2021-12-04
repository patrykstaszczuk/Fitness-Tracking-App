from abc import ABC
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token

from users import selectors


class UserInputValidation(ABC):

    def validate_password(self) -> None:
        if not self.password:
            return
        if self.password != self.password2:
            raise ValidationError('Passwords do not match')
        if len(self.password) < 5:
            raise ValidationError('Password too short')

    def validate_height(self) -> None:
        if not self.height:
            return
        if not 100 <= self.height <= 250:
            raise ValidationError(
                'Incorrect value for height, must be in <100, 250>)')

    def validate_weight(self) -> None:
        if not self.weight:
            return
        if not 20 <= self.weight <= 300:
            raise ValidationError(
                'Incorrect value for weight, must be in <20, 300>')

    def validate_age(self) -> None:
        if not self.age:
            return
        if not 10 <= self.age <= 120:
            raise ValidationError(
                'Incorrect value for age, must be in <10, 120>')

    def validate_gender(self) -> None:
        if not self.gender:
            return
        if self.gender not in ['Male', 'Female']:
            raise ValidationError(
                'Incorrect value for gender, must be either "Male" \
                or "Female"')

    def validate_name(self) -> None:
        if not self.name:
            return
        if len(self.name) > 255:
            raise ValidationError('Name too long, max lenght 20 chars')
        if get_user_model().objects.filter(name=self.name).exists():
            raise ValidationError('User with given name already exists')

    def validate_email(self) -> None:
        if not self.email:
            return
        if get_user_model().objects.filter(email=self.email).exists():
            raise ValidationError('User with given email already exists')


@dataclass
class CreateUserDto(UserInputValidation):
    email: str
    name: str
    password: str
    password2: str
    age: int = None
    height: int = None
    weight: int = None
    gender: str = None

    def __post_init__(self):
        self.validate_email()
        self.validate_name()
        self.validate_password()
        self.validate_age()
        self.validate_height()
        self.validate_weight()
        self.validate_gender()


class CreateUser:
    def create(self, dto: CreateUserDto):
        user = get_user_model().objects.create_user(
            email=dto.email,
            password=dto.password,
            name=dto.name,
            age=dto.age,
            height=dto.height,
            weight=dto.weight,
            gender=dto.gender

        )
        return user


@dataclass
class UpdateUserProfileDto(UserInputValidation):
    email: str = None
    name: str = None
    age: int = None
    height: int = None
    weight: int = None
    gender: str = None

    def __post_init__(self):
        self.validate_email()
        self.validate_name()
        self.validate_age()
        self.validate_height()
        self.validate_weight()
        self.validate_gender()


class UpdateUserProfile:
    def update(self, user: get_user_model, dto: UpdateUserProfileDto):
        for attr in vars(dto):
            value = getattr(dto, attr)
            if not value:
                continue
            setattr(user, attr, value)
        user.save()
        self._set_new_name_for_group(user)

    @staticmethod
    def _set_new_name_for_group(user: get_user_model) -> None:
        user.own_group.set_name()
        user.own_group.save()


@dataclass
class UpdateUserPasswordDto(UserInputValidation):
    old_password: str
    password: str
    password2: str

    def __post_init__(self) -> None:
        self.validate_password()


class UpdateUserPassword:
    def update(self, user: get_user_model, dto: UpdateUserPasswordDto) -> None:
        self._check_old_password(user, dto.old_password)
        user.set_password(dto.password)
        user.save()

    @staticmethod
    def _check_old_password(user: get_user_model, password: str) -> None:
        if not user.check_password(password):
            raise ValidationError('Old password is incorrect')


@dataclass
class CreateTokenDto:
    email: str
    password: str


class CreateToken:
    def create(self, dto: CreateTokenDto):
        user = selectors.user_authenticate(
            email=dto.email,
            password=dto.password
        )

        token, created = Token.objects.get_or_create(user=user)
        return token
