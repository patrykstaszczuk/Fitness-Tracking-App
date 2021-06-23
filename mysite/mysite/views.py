from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'account': reverse('users:profile', request=request, format=format),
        'fitness': reverse('health:health-diary', request=request, format=format),
        'meals-tracker': reverse('meals_tracker:api-root', request=request, format=format),
        'recipes': reverse('recipe:api-root', request=request, format=format),
    })
