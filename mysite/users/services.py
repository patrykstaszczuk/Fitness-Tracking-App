from users import selectors
import datetime
import time
from mysite import settings
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from users.models import StravaActivity, StravaApi, MyUser, Group

from dataclasses import dataclass


@dataclass
class UserService:
    data: dict
    user: get_user_model = None

    def create(self):
        """ create user """
        password = self.data.pop('password')
        self.user = MyUser(**self.data)
        self.user.set_password(password)
        try:
            self.user.save()
            self.create_m2m_instance()
            return self.user
        except IntegrityError:
            raise ValidationError('User with given email already exists')

    def update(self):
        """ update user instance """
        for attr in self.data:
            setattr(self.user, attr, self.data[attr])
        self.user.save()
        return self.user

    def change_password(self):
        """ change user password """
        old_password = self.data.pop('old_password')
        new_password = self.data.pop('new_password')
        confirm_password = self.data.pop('confirm_password')

        if not self.user.check_password(old_password):
            raise ValidationError('Old password is incorrect!')
        if new_password != confirm_password:
            raise ValidationError('Passwords do not match!')
        self.user.set_password(new_password)
        self.user.save()

    def create_m2m_instance(self):
        """ create m2m instance """
        Group.objects.create(founder=self.user)
        StravaApi.objects.create(user=self.user)

    def validate(self):
        """ validate input data """
        password = self.data.get('password')
        password2 = self.data.pop('password2')
        if password != password2:
            raise ValidationError('Passsowrds do not match')

        name = self.data.get('name')
        email = self.data.get('email')
        if get_user_model().objects.filter(email=email).exists():
            raise ValidationError(f'User with  email {email} already exists')
        if get_user_model().objects.filter(name=name).exists():
            raise ValidationError(f'User with name {name} already exists')

    def validate_update_data(self):
        """ validate data during update """
        name = self.data.get('name')
        email = self.data.get('email')
        if get_user_model().objects.filter(email=email).exclude(id=self.user.id).exists():
            raise ValidationError(f'User with  email {email} already exists')
        if get_user_model().objects.filter(name=name).exclude(id=self.user.id).exists():
            raise ValidationError(f'User with name {name} already exists')


@dataclass
class GroupService:
    user: get_user_model
    data: dict

    def send_group_invitation(self) -> None:
        """ send invitation to given users """
        for user_id in self.data['ids']:
            try:
                invited_user = selectors.user_get_by_id(user_id)
            except ObjectDoesNotExist as e:
                raise ValidationError(e)
            if invited_user == self.user:
                raise ValidationError('You cannot invite yourself')
            invited_user.pending_membership.add(self.user.own_group.id)

    def accept_group_invitation(self) -> None:
        """ accept given group invitations """
        for id in self.data['ids']:
            self.user.membership.add(id)
            self.user.pending_membership.remove(id)

    def deny_group_invitation(self) -> None:
        """ deny group invitations """
        for id in self.data['ids']:
            self.user.pending_membership.remove(id)

    def leave_group(self) -> None:
        """ leave group """
        for id in self.data['ids']:
            if self.user.own_group.id == id:
                raise ValidationError('You cannot leave own group!')
            self.user.membership.remove(id)

    def validate_pending_membership(self) -> None:
        """ validate that given group ids are in user pending membership """
        pending_membership = selectors.user_get_group_pending_membership(
            self.user).values_list('id', flat=True)
        for id in self.data['ids']:
            if id not in pending_membership:
                raise ValidationError(
                    f'You were not invited to group with id {id}')

    def validate_membership(self) -> None:
        """ validate that given group ids are in user membership """
        membership = selectors.group_get_membership(
            self.user).values_list('id', flat=True)
        for id in self.data['ids']:
            if id not in membership:
                raise ValidationError(
                    f'You are not a member of group with id {id}')


def authorize_to_strava(user: get_user_model, strava_code: str) -> bool:
    try:
        client_id, client_secret = selectors.get_environ_variables()
    except KeyError:
        return False
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": strava_code,
        "grant_type": "authorization_code"
    }
    strava_obj = StravaApi.objects.get_or_create(user=user)[0]
    url = settings.STRAVA_AUTH_URL
    res = selectors.process_request(
        strava_obj, url=url, payload=payload, type='POST')
    if res:
        important_auth_data = {'expires_at': None, 'refresh_token': None,
                               'access_token': None}
        if all(attr in res for attr in important_auth_data.keys()):
            for data in important_auth_data.keys():
                setattr(strava_obj, data, res[data])
            strava_obj.save()
            return True
        return False


def update_activities(user: get_user_model, date: datetime) -> None:
    """ get list of activities from strava for given day
    and add every new activities for db"""
    now = time.time()
    hour = 3600
    raw_strava_activities = []
    if now - selectors.get_strava_last_request_epoc_time(user=user) > hour:
        raw_strava_activities = selectors.get_activities_from_strava(
            user=user, date=date)
        process_and_save_strava_activities(user, raw_strava_activities)
    else:
        print('To many request try again soon')


def process_and_save_strava_activities(user: get_user_model, raw_strava_activities: list) -> None:
    """ convert raw activities into StravaActivity objects
    """
    if raw_strava_activities and isinstance(raw_strava_activities, list):
        activity_objects = []
        for activity in raw_strava_activities:
            strava_id = activity.get('id', None)
            if not strava_id:
                continue
            url = selectors.prepare_strava_request_url(id=strava_id)
            header = selectors.prepare_authorization_header(
                strava_obj=user.strava)
            strava_activity = selectors.process_request(
                user.strava, url, header, 'GET')
            if strava_activity:
                defaults = selectors.get_activity_properties(strava_activity)
                obj, created = StravaActivity.objects.update_or_create(
                    strava_id=strava_id, user=user, **defaults)
                activity_objects.append(obj)
        return activity_objects
    return None
    return None
