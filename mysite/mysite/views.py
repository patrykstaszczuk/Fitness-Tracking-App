from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import generics


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'account': reverse('users:profile', request=request, format=format),
        'fitness': reverse('health:dashboard', request=request, format=format),
        'meals-tracker': reverse('meals_tracker:api-root', request=request, format=format),
        'food': reverse('recipe:api-root', request=request, format=format),
    })


def get_serializer_required_fields(serializer):
    """ return fields names which are required """
    try:
        list = [f for f, v in serializer.get_fields().items()
                if getattr(v, 'required', True)]
        if not list:
            return None
        return list
    except AttributeError:
        return None


class RequiredFieldsResponseMessage(generics.GenericAPIView):
    """ create custom init for descendants """

    def get_serializer(self, *args, **kwargs):
        """ set serializers required fields private variable """
        serializer_instance = super().get_serializer()
        self._serializer_required_fields = get_serializer_required_fields(serializer_instance)
        return super().get_serializer(*args, **kwargs)

    def get_renderer_context(self):
        """ add links to response """
        context = super().get_renderer_context()
        context['required'] = self._serializer_required_fields
        app_name = self.request.resolver_match.app_name
        if hasattr(self, 'action') and self.basename is not None:
            if self.action == 'retrieve':
                links = {
                    f'{self.basename}-list': reverse(f'{app_name}:{self.basename}-list',
                                                     request=self.request),
                }
            else:
                links = None
            context['links'] = links
        return context

    def __init__(self, *args, **kwargs):
        self._serializer_required_fields = None
        super().__init__(*args, **kwargs)
