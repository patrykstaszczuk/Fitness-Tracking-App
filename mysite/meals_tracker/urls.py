from django.urls import path, include
from rest_framework.routers import DefaultRouter
from meals_tracker import views


app_name = 'meals_tracker'

urlpatterns = [
    path('meals/available-dates/', views.MealsAvailableDatesApi.as_view(),
         name='meal-available-dates'),
    path('meals/create', views.MealsTrackerCreateApi.as_view(), name='meal-create'),
    path('meals/<pk>/update',
         views.MealsTrackerUpdateApi.as_view(), name='meal-update'),
    path('meals/', views.MealsTrackerListApi.as_view(), name='meal-list'),
    path('meals/<pk>/delete',
         views.MealsTrackerDeleteApi.as_view(), name='meal-delete'),
    path('categories/', views.MealCategoryApi.as_view(),
         name='categories')
]
