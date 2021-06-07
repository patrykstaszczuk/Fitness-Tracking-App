from rest_framework import serializers
from meals_tracker import models


class MealsTrackerSerializer(serializers.ModelSerializer):
    """ serializer for meal objects """

    class Meta:
        model = models.Meal
        fields = '__all__'
        read_only_fields = ('id', 'user', 'date')
