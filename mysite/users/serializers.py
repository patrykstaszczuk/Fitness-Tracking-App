from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from users.models import Group, StravaActivity
from django.core.validators import ValidationError


class DynamicFieldsModelSerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)

            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserOutputSerializer(serializers.ModelSerializer):
    """ serializer for reading User model """

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'name', 'gender', 'age',
                  'height', 'weight')


class UserInputSerializer(serializers.Serializer):
    """ serializer for User model and input data """

    choices = (
        ('Male', 'Male'),
        ('Female', 'Female')
        )
    email = serializers.EmailField(required=True, min_length=3)
    name = serializers.CharField(required=True)
    age = serializers.IntegerField(required=False, min_value=0, max_value=50)
    height = serializers.IntegerField(
        required=False, min_value=40, max_value=300)
    weight = serializers.IntegerField(
        required=False, min_value=5, max_value=600)
    gender = serializers.ChoiceField(choices, required=False)
    password = serializers.CharField(required=True, min_length=5)
    password2 = serializers.CharField(required=True, min_length=5)


class UserUpdateInputSerializer(UserInputSerializer):
    """ serializer for updating user instance with no required fields """
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True)
    password = None
    password2 = None


class UserTokenInputSerializer(serializers.Serializer):
    """ serialier for user authentication object """

    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True,
                                     style={'input_type': 'password'},
                                     trim_whitespace=False
                                     )


class UserPasswordInputSerializer(serializers.Serializer):
    """ serializer for password change """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=5)
    confirm_password = serializers.CharField(required=True)


class UserGroupOutputSerializer(serializers.ModelSerializer):
    """ Serializer for handling groups """

    class Meta:
        model = Group
        fields = ('id', 'name', 'founder', 'members')
        read_only_fields = ('id', 'name', 'founder',)

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
    ids = serializers.ListField(child=serializers.IntegerField())



class StravaActivitySerializer(serializers.ModelSerializer):
    """ serializer for Strava activity model """

    class Meta:
        model = StravaActivity
        fields = '__all__'
