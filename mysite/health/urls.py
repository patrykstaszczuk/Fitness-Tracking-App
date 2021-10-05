from django.urls import path, include
from health import views

from rest_framework.routers import DefaultRouter

app_name = 'health'

urlpatterns = [
    path('bmi/', views.BMIRetrieveApi().as_view(), name='bmi-get'),
    path('daily/', views.RetrieveHealthDiary.as_view(), name='health-diary'),
    path('daily/update', views.UpdateHealthDiary.as_view(),
         name='health-diary-update'),
    path('raports/', views.HealthRaportList.as_view(), name='health-raport-list'),
    path('raports/<slug>', views.HealthRaportDetail.as_view(),
         name='health-raport-detail'),
    path('raports/<slug>/update', views.HealthRaportUpdate.as_view(),
         name='health-raport-update'),
    path('raports/statistic-history/<slug>', views.HealthStatisticDetail.as_view(),
         name='health-statistic-history'),
    path('weekly-summary/', views.HealthWeeklySummary.as_view(),
         name='weekly-summary'),
    path('', views.Dashboard.as_view(), name='dashboard')
]
