from django.urls import path, include
from health import views

from rest_framework.routers import DefaultRouter
# from rest_framework import routers

router = DefaultRouter()
router.register('', views.HealthRaport, basename='health')
app_name = 'health'

urlpatterns = [
    path('bmi/', views.BmiViewSet.as_view({'get': 'retrieve'}), name='bmi'),
    path('', views.HealthDiary.as_view({'get': 'retrieve',
                                               'post': 'create',
                                               'put': 'update',
                                               'patch': 'update'}),
         name='health-diary'),
    path('raporty/', include(router.urls)),
    path('podsumowanie-tygodnia', views.HealthWeeklySummary,
         name='weekly-summary'),
]
