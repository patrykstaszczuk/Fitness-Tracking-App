from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views

app_name = 'recipe'


urlpatterns = [
    path('recipes/', views.RecipesApi.as_view(), name='recipe-list'),
    path('recipes/', views.RecipesApi.as_view(), name='recipe-create'),
    path('recipes/<slug>', views.RecipeDetailApi.as_view(), name='recipe-detail'),
    path('recipes/<slug>', views.RecipeDetailApi.as_view(), name='recipe-update'),
    path('recipes/<slug>/tags', views.RecipeTagsApi.as_view(), name='recipe-tags'),
    path('recipes/<slug>/ingredients',
         views.RecipeIngredientsApi.as_view(), name='recipe-ingredients'),
    path('recipes/<slug>/ingredients/<pk>',
         views.RecipeIngredientDetailApi.as_view(), name='recipe-ingredients-update'),
    path('recipes/group/<pk>/<slug>', views.GroupRecipeDetailApi.as_view(),
         name='group-recipe-detail'),
    path('recipes/group/<pk>/<slug>/tags',
         views.GroupRecipeTagsApi.as_view(), name='group-recipe-tags'),
    path('recipes/group/<pk>/<slug>/ingredients',
         views.GroupRecipeIngredientsApi.as_view(), name='group-recipe-ingredients'),

    path('tags/', views.TagsApi.as_view(), name='tag-list'),
    path('tags/', views.TagsApi.as_view(), name='tag-create'),
    path('tags/<slug>', views.TagDetailApi.as_view(), name='tag-detail'),
    path('tags/<slug>', views.TagDetailApi.as_view(), name='tag-delete'),
    path('tags/<slug>', views.TagDetailApi.as_view(), name='tag-update'),

    path('ingredients/', views.IngredientsApi.as_view(), name='ingredient-list'),
    path('ingredients/', views.IngredientsApi.as_view(), name='ingredient-create'),
    path('ingredients/<slug>', views.IngredientDetailApi.as_view(),
         name='ingredient-detail'),
    path('ingredients/<slug>/tags',
         views.IngredientTagsApi.as_view(), name='ingredient-tags'),
    path('ingredients/<slug>/units',
         views.IngredientUnitsApi.as_view(), name='ingredient-units'),
    path('available-units/', views.UnitListApi.as_view(),
         name='unit-list'),

]
