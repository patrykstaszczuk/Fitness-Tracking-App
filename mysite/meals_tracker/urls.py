from django.urls import path, include
from rest_framework.routers import DefaultRouter
from meals_tracker import views


app_name = 'meals_tracker'

urlpatterns = [
    path('meals/', views.MealsApi.as_view(),
         name='meal-list'),
    path('meals/', views.MealsApi.as_view(),
         name='meal-create'),
    path('meals/<pk>', views.MealsDetailApi.as_view(), name='meal-detail'),
    path('meals/<pk>/recipes', views.MealsRecipesApi.as_view(), name='meal-recipes'),
    path('meals/<pk>/recipes/<recipe_pk>',
         views.MealsRecipesDetailApi.as_view(), name='meal-recipes-detail'),
    path('meals/<pk>/ingredients',
         views.MealsIngredientsApi.as_view(), name='meal-ingredients'),
    path('meals/<pk>/ingredients/<ingredient_pk>',
         views.MealsIngredientsDetailApi.as_view(), name='meal-ingredients-detail'),
    path('meals-history/', views.MealsAvailableDatesApi.as_view(),
         name='meal-available-dates'),
     path('categories/', views.MealCategoryApi.as_view(),
          name='categories')

    ]
#
