from rest_framework import serializers
from health.models import HealthDiary
import datetime
from users.serializers import StravaActivitySerializer
from users import selectors as users_selectors
from django.core.exceptions import ValidationError


class HealthDiarySerializer(serializers.ModelSerializer):
    """ serializer for health diaries list """

    self = serializers.HyperlinkedIdentityField(
        view_name='health:health-diary-detail', lookup_field='slug')

    class Meta:
        model = HealthDiary
        fields = ('self', )


class HealthDiaryDetailSerializer(serializers.ModelSerializer):
    """ serializer for retreiving HealthDiary objects"""

    activities = serializers.SerializerMethodField()

    class Meta:
        model = HealthDiary
        exclude = ('last_update', )

    def get_activities(self, obj):
        """ get activities for given day """

        if isinstance(obj.date, str):
            try:
                obj.date = datetime.date.fromisoformat(obj.date)
            except ValidationError:
                return None
        activities = users_selectors.get_activities(
            user=obj.user, date=obj.date)
        for activity in activities:
            obj.burned_calories += activity.calories
        return StravaActivitySerializer(activities, many=True).data


class AddStatisticsSerializer(serializers.Serializer):
    """ serializer for incoming diary data """

    weight = serializers.FloatField(required=False)
    sleep_length = serializers.TimeField(required=False)
    rest_heart_rate = serializers.IntegerField(required=False)
    daily_thoughts = serializers.CharField(required=False, allow_blank=True)
