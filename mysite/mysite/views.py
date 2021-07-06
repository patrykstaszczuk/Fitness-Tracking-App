from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import generics


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'account': reverse('users:profile', request=request, format=format),
        'fitness': reverse('health:health-diary', request=request, format=format),
        'meals-tracker': reverse('meals_tracker:api-root', request=request, format=format),
        'food': reverse('recipe:api-root', request=request, format=format),
    })


def get_serializer_required_fields(serializer):
    """ return fields names which are required """
    try:
        return [f for f, v in serializer.get_fields().items() if getattr(v, 'required', True)]
    except AttributeError:
        return None


class RequiredFieldsResponseMessage(generics.RetrieveAPIView):
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
        if hasattr(self, 'action') and self.basename is not None:
            if self.action == 'retrieve':
                links = {
                    f'{self.basename}-list': reverse(f'recipe:{self.basename}-list',
                                                     request=self.request),
                }
            else:
                links = None
            context['links'] = links
        return context

    def __init__(self, *args, **kwargs):
        self._serializer_required_fields = []
        super().__init__(*args, **kwargs)
