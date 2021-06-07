from django.urls import path, include
from rest_framework.routers import DefaultRouter
from meals_tracker import views

router = DefaultRouter()
router.register('', views.MealsTrackerViewSet)
app_name = 'meals_tracker'

urlpatterns = [
    path('', include(router.urls))
]
