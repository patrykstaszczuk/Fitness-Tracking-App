from django.urls import path, include
from health import views

from rest_framework.routers import DefaultRouter

app_name = 'health'

urlpatterns = [

    path('diaries/<slug>', views.HealthDiaryDetailApi.as_view(),
         name='health-diary-detail'),
    path('diaries/', views.HealthDiaryApi.as_view(), name='health-diary-list'),
    path('bmi/', views.BMIRetrieveApi().as_view(), name='bmi-get'),
    path('statistics/<name>', views.HealthStatisticApi.as_view(),
         name='health-statistic'),
    path('weekly-summary/', views.HealthWeeklySummary.as_view(),
         name='weekly-summary'),
    path('', views.Dashboard.as_view(), name='dashboard')
]
