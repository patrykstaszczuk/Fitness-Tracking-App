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
        'height', 'weight', 'groups')

class UserInputSerializer(DynamicFieldsModelSerializer):
    """ serializer for User model and input data """

    choices = (
        ('Male', 'Male'),
        ('Female', 'Female')
        )
    email = serializers.EmailField(required=False)
    name = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    password2 = serializers.CharField(write_only=True, required=False)
    age = serializers.IntegerField(required=False)
    height = serializers.IntegerField(required=False)
    weight = serializers.IntegerField(required=False)
    gender = serializers.ChoiceField(choices, required=False)

    def is_valid(self, raise_exception=False):
        """ pop password2 """
        is_valid = super().is_valid(raise_exception)
        if 'password2' in self.validated_data:
            self.validated_data.pop('password2')
        return is_valid

    def validate(self, values):
        """ validate passwords matching """
        password = values.get('password')
        password2 = values.get('password2')
        if password != password2:
            raise serializers.ValidationError('Password do not match!')
        return values

    def validate_password(self, password):
        """ validate password length """
        if len(password) < 5:
            raise serializers.ValidationError('Password is too short')
        return password

    def validate_name(self, name):
        """ validate name length """
        if len(name) < 3:
            raise serializers.ValidationError('Username is to short')
        return name

    def validate_age(self, age):
        """ validate age """
        if not 0 < age <= 150:
            raise serializers.ValidationError('Incorrect age')
        return age

    def validate_height(self, height):
        """ validate height """

        if not 40 < height <= 300:
            raise serializers.ValidationError('Incorrect height')
        return height

    def validate_weight(self, weight):
        """ validate weight """

        if not 5 < weight <= 600:
            raise serializers.ValidationError('Incorrect weight')
        return weight


class AuthTokenSerializer(serializers.Serializer):
    """ serialier for user authentication object """

    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        """ validate and authenticate the user """
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            msg = ('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authentication')

        attrs['user'] = user
        return attrs


class MembershipSerializer(serializers.ModelSerializer):
    """ serializer for handling memberships """
    class Meta:
        model = get_user_model()
        fields = ('membership', )
        read_only_fields = ('membership', )


class GroupOutputSerializer(serializers.ModelSerializer):
    """ Serializer for handling groups """

    class Meta:
        model = Group
        fields = ('id', 'name', 'founder',)
        read_only_fields = ('id', 'name', 'founder',)

class UserIdSerializer(serializers.Serializer):
    """ serialzier for user id """
    id = serializers.IntegerField()

class GroupInputSerializer(serializers.Serializer):
    """ serializing inpout data. Need to use nested serialzier due to problem with accessing data when using ListField """
    pending_membership = UserIdSerializer(required=False, many=True, write_only=False)


class SendInvitationSerializer(serializers.ModelSerializer):
    """ serializer for sending invitation to other users """

    class Meta:
        model = Group
        fields = ('pending_membership', )
        extra_kwargs = {'pending_membership': {'error_messages':
                        {'does_not_exist': 'User with provided id does not exits'}}}

    def validate_pending_membership(self, users):
        """ check if founder id is in invated users list """
        if self.context['request'].user in users:
            raise serializers.ValidationError("You cannot invite yourself!")
        return users


class ManageInvitationSerializer(serializers.ModelSerializer):
    """ serializer for managing groups invitation and acctepting/denying group
    invitations with action field """

    action = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = get_user_model()
        fields = ('pending_membership', 'action')

    def validate_action(self, action):
        """ validate action value """
        if action not in range(2):
            raise ValidationError('Incorrect value for action')
        self.fields.pop('action')
        return action

    def validate_pending_membership(self, groups):
        """ validating that requested group is in pending membership
        relation """

        for group in groups:
            if group not in self.instance.pending_membership.all():
                raise ValidationError(f"{group.id} such group does \
                        not exists in your pending membership")
        return groups

    def save(self, **kwargs):
        """ update pending_membership and membership fields """
        user = self.instance
        groups = self.validated_data.get('pending_membership')
        action = self.validated_data.pop('action')
        groups_ids = [group.id for group in groups]
        if action:
            user.membership.add(*groups_ids)
            user.pending_membership.remove(*groups_ids)
        else:
            user.pending_membership.remove(*groups_ids)

        return self.instance


class LeaveGroupSerializer(serializers.Serializer):
    """ serializer for leaving group """

    id = serializers.IntegerField(required=True, write_only=True)
    groups = serializers.SerializerMethodField()

    def get_groups(self, obj):
        """ get memberships """
        return GroupSerializer(self.instance.get_memberships().exclude(founder=self.instance),
                               many=True).data

    def validate_id(self, value):
        """ check if user accually belongs to provided group """
        try:
            group = Group.objects.get(id=value)
        except Group.DoesNotExist:
            raise serializers.ValidationError('Group does not exists')
        if group.founder == self.instance:
            raise serializers.ValidationError('You cannot leave your own group')
        return value

    def save(self, **kwargs):
        """ remove user from group """
        group = self.validated_data.pop('id')
        if group:
            self.instance.membership.remove(group)


class StravaActivitySerializer(serializers.ModelSerializer):
    """ serializer for Strava activity model """

    class Meta:
        model = StravaActivity
        fields = '__all__'
