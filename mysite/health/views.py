from rest_framework import status, authentication, permissions
from rest_framework.decorators import authentication_classes, permission_classes

from rest_framework.response import Response
from health import serializers
from health import selectors, services
import datetime


from mysite.views import BaseAuthPermClass
from mysite.exceptions import ApiErrorsMixin


from rest_framework.views import APIView
from rest_framework.reverse import reverse


from users import selectors as users_selectors
from users import services as users_services


class Dashboard(APIView):
    """ main view for Health app """
    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        """ return possible action for health app """

        data = {
            'bmi': reverse('health:bmi', request=request),
            'daily': reverse('health:health-diary', request=request),
            # 'raports/': reverse('health:health-list', request=request),
            # 'weekly-summary/': reverse('health:weekly-summary', request=request),

        }
        return Response(data=data, status=status.HTTP_200_OK)


class BaseHealthAppView(BaseAuthPermClass, ApiErrorsMixin, APIView):
    """ base class for all health app views """

    def set_location_in_header(self, request, slug: str = None) -> dict:
        """ set location with proper url in header """
        if slug:
            return {'Location': reverse('health:health-raport-detail',
                                        request=request,
                                        kwargs={'slug': slug})}
        return {'Location': reverse('health:health-diary', request=request)}


class BMIRetrieveApi(BaseHealthAppView):
    """ API for retrieving BMI for authenticated user """

    def get(self, request, *args, **kwargs):
        """ get BMI """
        bmi = users_selectors.get_bmi(user=request.user)
        return Response(data={'bmi': bmi}, status=status.HTTP_200_OK)


class RetrieveHealthDiary(BaseHealthAppView):
    """ API for retrieving daily health diary """

    def get(self, request, *args, **kwargs):
        """ return heatlth data for today """
        now = datetime.date.today()
        users_services.update_activities(user=request.user, date=now)
        health_diary_instance = selectors.health_get_diary(user=request.user)
        serializer = serializers.HealthDiaryOutputSerializer(
            instance=health_diary_instance)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class UpdateHealthDiary(BaseHealthAppView):
    """ API for updating health diary """

    def patch(self, request, *args, **kwargs):
        """ handle post request """
        today = datetime.date.today()
        diary = selectors.get_health_diary(user=request.user, date=today)
        serializer = serializers.HealthDiaryInputSerializer(data=request.data)
        if serializer.is_valid():
            health_service = services.HealthService(
                user=request.user, data=serializer.data, instance=diary)
            health_service.update()
            headers = self.set_location_in_header(request)
            return Response(status=status.HTTP_200_OK, headers=headers)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HealthRaportList(BaseHealthAppView):
    """ API for retrieving health raports entries """

    def get(self, request, *args, **kwargs):
        """ return health raports entries """
        health_diaries = selectors.health_get_past_diaries(user=request.user)
        serializer = serializers.HealthDiaryOutputSerializer(
            health_diaries, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class HealthRaportDetail(BaseHealthAppView):
    """ API for retrieving health raport  """

    def get(self, request, *args, **kwargs):
        """ return health raport detail"""
        slug = kwargs.get('slug')
        heatlh_diary = selectors.health_get_past_diary(
            user=request.user, slug=slug)
        serializer = serializers.HealthDiaryOutputSerializer(heatlh_diary)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class HealthRaportUpdate(BaseHealthAppView):
    """ API for updating health raport """

    def patch(self, request, *args, **kwargs):
        """ update health raport """
        slug = kwargs.get('slug')
        heatlh_diary = selectors.health_get_past_diary(
            user=request.user, slug=slug)
        serializer = serializers.HealthDiaryInputSerializer(data=request.data)

        if serializer.is_valid():
            health_service = services.HealthService(
                user=request.user,
                instance=heatlh_diary,
                data=serializer.data
            )
            instance = health_service.update()
            headers = self.set_location_in_header(request=request,
                                                  slug=instance.slug)
            return Response(status=status.HTTP_200_OK, headers=headers)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HealthStatisticDetail(BaseHealthAppView):
    """ API for retrieving heatlh statistic raport """

    def get(self, request, *args, **kwargs):
        """ return health statistic raport """
        slug = kwargs.get('slug')
        all_field_values = selectors.get_all_values_for_given_field(
            request.user, slug)
        return Response(data=list(all_field_values), status=status.HTTP_200_OK)


class HealthWeeklySummary(BaseHealthAppView):
    """ API for retrieving weekly summary """

    def get(self, request, *args, **kwargs):
        """ retrieve weekly summary """
        weekly_summary = selectors.get_weekly_avg_stats(user=request.user)
        if weekly_summary == {}:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(data=weekly_summary,
                        status=status.HTTP_200_OK)
