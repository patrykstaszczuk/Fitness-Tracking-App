from django.urls import path
from health import views
# from rest_framework import routers

app_name = 'health'

urlpatterns = [
    path('bmi/', views.BmiViewSet.as_view({'get': 'retrieve'}), name='bmi'),
    path('dzisiaj/', views.HealthDiary.as_view({'get': 'retrieve',
                                               'post': 'create',
                                                'put': 'update',
                                                'patch': 'update'}),
         name='health-diary')
]
