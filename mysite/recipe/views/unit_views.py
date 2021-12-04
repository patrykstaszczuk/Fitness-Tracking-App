from rest_framework.response import Response
from rest_framework import status

from .base_views import BaseViewClass
from recipe import selectors, serializers


class UnitListApi(BaseViewClass):
    """ viewfor retrieving available units """

    def get(self, request, *args, **kwargs):
        """ return all avilable units """
        units = selectors.unit_list()
        if units.count() > 0:
            serializer = serializers.UnitOutputSerializer(units, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)
