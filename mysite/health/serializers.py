from rest_framework import serializers
from health import models
import datetime
from users.serializers import DynamicFieldsModelSerializer
from django.contrib.auth import get_user_model


class HealthDiarySerializer(serializers.ModelSerializer):
    """ serializer for health diary """

    class Meta:
        model = models.HealthDiary
        fields = '__all__'
        read_only_fields = ('id', 'user', 'date', 'slug')

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

    def validate_calories(self, value):
        """ validate calories """

        if value is not None and not 0 < value < 20000:
            raise serializers.ValidationError('Nieporawna liczba kalorii')
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
        read_only_fields = ('id', 'user', 'date', 'slug')
        model = models.HealthDiary


class HealthStatisticHistorySerializer(DynamicFieldsModelSerializer):
    """ serializer for specific statistic history """

    class Meta:
        model = models.HealthDiary
        exclude = ('id', 'slug', 'user', 'date', 'daily_thoughts')
