from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from mysite.renderers import CustomRenderer
from mysite.views import BaseAuthPermClass
from mysite.exceptions import ApiErrorsMixin


class BaseViewClass(BaseAuthPermClass, ApiErrorsMixin, APIView):
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )
    renderer_classes = [CustomRenderer, ]

    def get_serializer_context(self):
        """ Extra context provided to the serializer class. """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }
