from django.urls import path, include
from health import views

from rest_framework.routers import DefaultRouter
# from rest_framework import routers

router = DefaultRouter()
router.register('', views.HealthRaport, basename='health')
app_name = 'health'

urlpatterns = [
    path('bmi/', views.BmiViewSet.as_view({'get': 'retrieve'}), name='bmi'),
    path('daily/', views.HealthDiary.as_view(retrieve),
         name='health-diary'),
    path('raports/', include(router.urls)),
    path('weekly-summary/', views.HealthWeeklySummary.as_view(),
         name='weekly-summary'),
    path('', views.Dashboard.as_view(), name='dashboard')
]
