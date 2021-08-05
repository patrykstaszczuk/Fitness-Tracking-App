from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import generics, fields


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'account': reverse('users:profile', request=request, format=format),
        'fitness': reverse('health:dashboard', request=request, format=format),
        'meals-tracker': reverse('meals_tracker:api-root', request=request, format=format),
        'food': reverse('recipe:api-root', request=request, format=format),
    })


def get_serializer_fields(serializer):
    """ return fields names which are required """

    required_fields = []
    writable_fields = []
    for f, v in serializer.get_fields().items():
        field_type = str(type(v))[23:-2]
        if getattr(v, 'required', True):
            required_fields.append(f)
        if not getattr(v, 'read_only'):
            writable_fields.append({"name": f, "type": field_type})

    return required_fields, writable_fields


class RequiredFieldsResponseMessage(generics.GenericAPIView):
    """ create custom init for descendants """

    def get_serializer(self, *args, **kwargs):
        """ set serializers required fields private variable """
        serializer_instance = super().get_serializer()
        self._serializer_fields = get_serializer_fields(serializer_instance)
        return super().get_serializer(*args, **kwargs)

    def get_renderer_context(self):
        """ add links to response """
        context = super().get_renderer_context()
        if self._serializer_fields:
            context['required'] = self._serializer_fields[0]
            context['writable'] = self._serializer_fields[1]
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
        self._serializer_fields = None
        super().__init__(*args, **kwargs)
