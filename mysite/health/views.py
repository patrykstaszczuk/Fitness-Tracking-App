from rest_framework import viewsets, mixins, status
from rest_framework import authentication, permissions
from rest_framework.response import Response


class BmiViewSet(viewsets.GenericViewSet):
    """ View for retrieving information about BMI from user model """

    authentication_classes = (authentication.TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def retrieve(self, request, *args, **kwargs):
        """ retrieve user's BMI """

        bmi = request.user.get_bmi()
        return Response(data={'bmi': bmi}, status=status.HTTP_200_OK)
