from rest_framework import serializers
from health import models
import datetime


class HealthDiarySerializer(serializers.ModelSerializer):
    """ serializer for health diary """

    class Meta:
        model = models.HealthDiary
        fields = '__all__'
        read_only_fields = ('user', 'date')

    def save(self, **kwargs):
        """ if requested user already have health diary for today, update it
        regardless POST request"""

        user = kwargs.get('user')
        now = datetime.date.today()

        try:
            self.instance = models.HealthDiary.objects. \
                filter(user=user).get(date=now)
        except models.HealthDiary.DoesNotExist:
            self.instance = None
        super().save(**kwargs)

    def validate_weight(self, weight):
        """ validate weight """

        if not 5 < weight <= 600:
            raise serializers.ValidationError('Niepoprawna waga')
        return weight

    def validate_sleep_length(self, sleep_length):
        """ validate sleep_length """

        if not 0 < sleep_length <= 24:
            raise serializers.ValidationError('Niepoprawna długość snu!')
        return sleep_length

    def validate_rest_heart_rate(self, rest_heart_rate):
        """ validate rest_heart_rate """

        if not 0 < rest_heart_rate < 200:
            raise serializers.ValidationError('Nieporawna wartość tętna \
                                              spoczynkowego')
        return rest_heart_rate

    def validate_calories(self, calories):
        """ validate calories """

        if not 0 < calories < 20000:
            raise serializers.ValidationError('Nieporawna liczba kalorii')
        return calories

    def validate_daily_thoughts(self, daily_thoughts):
        """ validated length of daily_thoughts """

        if len(daily_thoughts) > 2000:
            raise serializers.ValidationError('Maksymalna liczba znaków: 2000')
        return daily_thoughts
