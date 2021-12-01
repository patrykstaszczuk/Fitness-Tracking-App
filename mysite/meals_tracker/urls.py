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

    ]
#
# path('meals/available-dates/', views.MealsAvailableDatesApi.as_view(),
#      name='meal-available-dates'),
# path('meals/<pk>/update',
#      views.MealsTrackerUpdateApi.as_view(), name='meal-update'),
# path('meals/', views.MealsTrackerListApi.as_view(), name='meal-list'),
# path('meals/<pk>/delete',
#      views.MealsTrackerDeleteApi.as_view(), name='meal-delete'),
# path('categories/', views.MealCategoryApi.as_view(),
#      name='categories')
#      name='categories')
