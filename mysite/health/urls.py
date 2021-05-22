from django.urls import path
from health import views

app_name = 'health'

urlpatterns = [
    path('bmi/', views.BmiViewSet.as_view({'get': 'retrieve'}), name='bmi'),
]
