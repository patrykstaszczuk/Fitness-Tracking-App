from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from users.models import Group, StravaActivity
from django.core.validators import ValidationError


class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)

            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserSerializer(DynamicFieldsModelSerializer):
    """ serializer for MyUser instances handling """

    password2 = serializers.CharField(label='Confirm password', write_only=True)

    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'password2', 'name', 'age', 'gender',
                  'height', 'weight')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """ create a new user with encrypted password and return it """
        validated_data.pop('password2')
        return get_user_model().objects.create_user(**validated_data)

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


class UserChangePasswordSerializer(serializers.Serializer):
    """ update user password """
    old_password = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(min_length=8, required=True,
                                     write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect!")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance.set_password(password)
        instance.save()
        return instance


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


class GroupSerializer(serializers.ModelSerializer):
    """ Serializer for handling groups """

    class Meta:
        model = Group
        fields = ('id', 'name', 'founder',)
        read_only_fields = ('id', 'name', 'founder',)


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
