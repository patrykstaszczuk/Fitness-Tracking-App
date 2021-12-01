from rest_framework import status, authentication, permissions
from rest_framework.decorators import authentication_classes, permission_classes

from rest_framework.response import Response
from rest_framework.request import Request
from health import serializers
from health import selectors, services
import datetime


from mysite.views import BaseAuthPermClass
from mysite.exceptions import ApiErrorsMixin


from rest_framework.views import APIView
from rest_framework.reverse import reverse


from users import selectors as users_selectors
from users import services as users_services

from health.services import (
    AddStatisticsDto,
    AddStatistics,
)


class Dashboard(APIView):
    """ main view for Health app """
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        """ return possible action for health app """

        data = {
            'bmi': reverse('health:bmi-get', request=request),
            'diaries': reverse('health:health-diary-list', request=request),
            'weight': reverse('health:health-statistic', kwargs={'name': 'weight'}, request=request),
            'sleep_length': reverse('health:health-statistic', kwargs={'name': 'sleep_length'}, request=request),
            'rest_heart_rate': reverse('health:health-statistic', kwargs={'name': 'rest_heart_rate'}, request=request),
            # 'raports/': reverse('health:health-list', request=request),
            # 'weekly-summary/': reverse('health:weekly-summary', request=request),

        }
        return Response(data=data, status=status.HTTP_200_OK)


class BaseHealthView(BaseAuthPermClass, ApiErrorsMixin, APIView):
    """ base class for all health app views """

    def set_location_in_header(self, request, slug: str) -> dict:
        """ set location with proper url in header """
        return {'Location': reverse('health:health-diary-detail',
                                    request=request,
                                    kwargs={'slug': slug})}

    def get_serializer_context(self):
        """ Extra context provided to the serializer class. """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }


class HealthDiaryDetailApi(BaseHealthView):
    """ API for retreving and updating health diary """

    def post(self, request, *args, **kwargs):
        date = kwargs.get('slug')
        diary = selectors.health_diary_get(request.user, date)
        dto = self._prepare_dto(request)
        service = AddStatistics()
        service.add(diary, dto)
        headers = self.set_location_in_header(request, diary.slug)
        return Response(status=status.HTTP_200_OK, headers=headers)

    def get(self, request, *args, **kwargs):
        date = kwargs.get('slug')
        diary = selectors.health_diary_get(request.user, date)
        serializer = serializers.HealthDiaryDetailSerializer(diary)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def _prepare_dto(self, request: Request) -> AddStatisticsDto:
        serializer = serializers.AddStatisticsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return AddStatisticsDto(
            weight=data.get('weight'),
            sleep_length=data.get('sleep_length'),
            rest_heart_rate=data.get('rest_heart_rate'),
            daily_thoughts=data.get('daily_thoughts')
        )


class HealthDiaryApi(BaseHealthView):

    def get(self, request, *args, **kwargs):
        all_diaries = selectors.health_diary_list(user=request.user)
        serializer = serializers.HealthDiarySerializer(
            all_diaries, many=True, context=self.get_serializer_context())
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class BMIRetrieveApi(BaseHealthView):
    """ API for retrieving BMI for authenticated user """

    def get(self, request, *args, **kwargs):
        """ get BMI """
        bmi = users_selectors.get_bmi(user=request.user)
        return Response(data={'bmi': bmi}, status=status.HTTP_200_OK)


class HealthStatisticApi(BaseHealthView):
    """ API for retrieving heatlh statistic raport """

    def get(self, request, *args, **kwargs):
        """ return health statistic raport """
        slug = kwargs.get('name')
        all_field_values = selectors.get_all_values_for_given_field(
            request.user, slug)
        return Response(data=list(all_field_values), status=status.HTTP_200_OK)


class HealthWeeklySummary(BaseHealthView):
    """ API for retrieving weekly summary """

    def get(self, request, *args, **kwargs):
        """ retrieve weekly summary """
        weekly_summary = selectors.get_weekly_avg_stats(user=request.user)
        if weekly_summary == {}:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(data=weekly_summary,
                        status=status.HTTP_200_OK)
