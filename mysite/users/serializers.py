from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from users.models import Group, StravaActivity
from django.core.validators import ValidationError


class UserOutputSerializer(serializers.ModelSerializer):
    """ serializer for reading User model """

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'name', 'gender', 'age',
                  'height', 'weight')


class CreateUserSerializer(serializers.Serializer):
    """ serializer for User model and input data """

    choices = (
        ('Male', 'Male'),
        ('Female', 'Female')
        )
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True)
    age = serializers.IntegerField(required=False)
    height = serializers.IntegerField(required=False)
    weight = serializers.IntegerField(
        required=False)
    gender = serializers.ChoiceField(choices, required=False)
    password = serializers.CharField(required=True)
    password2 = serializers.CharField(required=True)


class CreateTokenSerializer(serializers.Serializer):
    """ serializer for token object retrieving """

    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class UpdateUserSerializer(CreateUserSerializer):
    """ serializer for updating user instance """
    email = serializers.EmailField(required=False)
    name = serializers.CharField(required=False)
    password = None
    password2 = None


class UpdateUserPasswordSerializer(serializers.Serializer):
    """ serializer for password change """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)


class UserGroupOutputSerializer(serializers.ModelSerializer):
    """ Serializer for handling groups """

    class Meta:
        model = Group
        fields = ('id', 'name', 'founder', 'members')

    def to_representation(self, instance):
        """ add status to groups """
        ret = super().to_representation(instance)
        try:
            status = None
            user = self.context['request'].user
            if ret['founder'] == user.id:
                status = 'owner'
            elif user.id in ret['members']:
                status = 'member'
            else:
                status = 'pending'
            ret.update({'status': status})
        except AttributeError:
            pass
        return ret


class IdSerializer(serializers.Serializer):
    """ serialzier for user id """
    id = serializers.IntegerField()


class StravaActivitySerializer(serializers.ModelSerializer):
    """ serializer for Strava activity model """

    class Meta:
        model = StravaActivity
        fields = '__all__'
