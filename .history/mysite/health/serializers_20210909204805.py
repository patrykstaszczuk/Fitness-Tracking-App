from rest_framework import serializers
from health import models
from health.models import HealthDiary
import datetime
from users.serializers import DynamicFieldsModelSerializer, \
                             StravaActivitySerializer
from users.models import StravaActivity
from users import selectors as users_selectors
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


class HealthDiaryOutputSerializer(serializers.ModelSerializer):
    """ serializer for retreiving HealthDiary objects"""

    activities = serializers.SerializerMethodField()
    calories_delta = serializers.SerializerMethodField()

    class Meta:
        model = HealthDiary
        fields = '__all__'


    def get_activities(self, obj):
        """ get activities for given day """

        if isinstance(obj.date, str):
            try:
                obj.date = datetime.date.fromisoformat(obj.date)
            except ValidationError:
                return None
        activities = users_selectors.get_activities(user=obj.user, date=obj.date)
        for activity in activities:
            obj.burned_calories += activity.calories
        return StravaActivitySerializer(activities, many=True).data

    def get_calories_delta(self, obj):
        """ get calories delta for calories intake and calories burned """
        return obj.calories - obj.burned_calories

class HealthDiaryOutputSerializer(serializers.Serializer):
    """ serializer for handling patch request for"""
class HealthDiarySerializer(serializers.ModelSerializer):
    """ serializer for health diary """

    activities = serializers.SerializerMethodField()
    calories_delta = serializers.SerializerMethodField()

    class Meta:
        model = models.HealthDiary
        fields = '__all__'
        read_only_fields = ('id', 'user', 'date', 'slug', 'calories',
                            'last_update', 'burned_calories')

    def get_activities(self, obj):
        """ get activities for given day """

        if isinstance(obj.date, str):
            try:
                obj.date = datetime.date.fromisoformat(obj.date)
            except ValidationError:
                return None

        activities = StravaActivity.objects.filter(user=obj.user,
                                                   date__date=datetime.date(obj.date.year,
                                                                            obj.date.month,
                                                                            obj.date.day))
        for activity in activities:
            obj.burned_calories += activity.calories
        return StravaActivitySerializer(activities, many=True).data

    def get_calories_delta(self, obj):
        """ get calories delta for calories intake and calories burned """
        return obj.calories - obj.burned_calories

    def save(self, **kwargs):
        """ if requested user already have health diary for today, update it
        regardless POST request"""

        user = kwargs.get('user')
        now = datetime.date.today()

        try:
            self.instance = models.HealthDiary.objects. \
                filter(user=user).get(date=now)
        except models.HealthDiary.DoesNotExist:
            pass
        super().save(**kwargs)

    def validate_weight(self, value):
        """ validate weight """

        if value is not None and not 5 < value <= 600:
            raise serializers.ValidationError('Niepoprawna waga')
        return value

    def validate_sleep_length(self, value):
        """ validate sleep_length """

        if value is not None and not 0 < value <= 24:
            raise serializers.ValidationError('Niepoprawna długość snu!')
        return value

    def validate_rest_heart_rate(self, value):
        """ validate rest_heart_rate """

        if value is not None and not 0 < value < 200:
            raise serializers.ValidationError('Nieporawna wartość tętna \
                                              spoczynkowego')
        return value

    def validate_daily_thoughts(self, value):
        """ validated length of daily_thoughts """

        if len(value) > 2000:
            raise serializers.ValidationError('Maksymalna liczba znaków: 2000')
        return value


class HealthRaportSerializer(serializers.ModelSerializer):
    """ serializer for health statistics raports and history list """

    url = serializers.HyperlinkedIdentityField(view_name='health:health-detail',
                                               lookup_field='slug')

    class Meta:
        exclude = ('daily_thoughts', )
        read_only_fields = ('id', 'user', 'date', 'slug',
                            'calories', 'last_update', 'burned_calories')
        model = models.HealthDiary


class HealthStatisticHistorySerializer(DynamicFieldsModelSerializer):
    """ serializer for specific statistic history """

    class Meta:
        model = models.HealthDiary
        exclude = ('id', 'slug', 'user', 'date', 'daily_thoughts')
