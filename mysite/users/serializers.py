from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from users.models import Group
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
    """ Serializer form the users object """

    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'name', 'age', 'sex')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """ create a new user with encrypted password and return it """
        return get_user_model().objects.create_user(**validated_data)


class UserChangePasswordSerializer(serializers.Serializer):
    """ update user password """
    old_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(min_length=8, required=True,
                                     write_only=True, trim_whitespace=False)

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

    class Meta:
        model = get_user_model()
        fields = ('membership', )
        read_only_fields = ('membership', )


class GroupSerializer(serializers.ModelSerializer):
    """ Serializer for group object """

    class Meta:
        model = Group
        fields = ('id', 'name', 'founder',)
        read_only_fields = ('id', 'name', 'founder',)

    def save(self, **kwargs):
        """ check if user have already own gorup, if yes raise error """
        founder = kwargs.get('founder')

        exist = Group.objects.filter(founder=founder)

        if exist:
            raise serializers.ValidationError('Możesz założyć tylko \
                                              jedną grupę')
        return super().save(**kwargs)

    def create(self, validated_data):
        """ override create to provide value's for name and members """
        instance = super().create(validated_data)
        instance.name = instance.founder.name + 's group'
        instance.members.add(instance.founder)
        instance.save()
        return instance


class SendInvitationSerializer(serializers.Serializer):
    """ serializer for sending invitation to other users """

    pending_membership = serializers.CharField(max_length=100)

    def update(self, instance, validated_data):
        """ update Group pending_membership field """

        user = validated_data.get('pending_membership')

        try:
            user = get_user_model().objects.get(email=user)
        except ValidationError:
            self.errors.update({'user': 'Taki użytkownik nie istnieje!'})
            raise ValidationError(self.errors)

        instance.pending_membership.add(user)
        return instance


class ManageInvitationSerializer(serializers.ModelSerializer):
    """ serializer for managing groups invitation and request acceptance """

    class Meta:
        model = get_user_model()
        fields = ('pending_membership', )

    def validate_pending_membership(self, groups):
        """ validating that requested group is in pending membership
        relation """

        for group in groups:
            try:
                get_user_model().objects.filter(pending_membership=group.id)
            except ValidationError:
                raise ValidationError("Taka grupa nie istnieje!")
        return groups

    def save(self, **kwargs):
        """ update pending_membership and membership fields """

        user = self.instance
        groups = self.validated_data.get('pending_membership')

        groups_ids = [group.id for group in groups]

        user.membership.add(*groups_ids)
        user.pending_membership.remove(*groups_ids)

        return self.instance
