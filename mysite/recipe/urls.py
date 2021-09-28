from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views

router = DefaultRouter()
#router.register('ingredients', views.IngredientViewSet)
#router.register('tags', views.TagViewSet, basename='tag')
# router.register('recipes', views.RecipeViewSet, basename='recipe')

app_name = 'recipe'


urlpatterns = [
    # path('', include(router.urls)),
    path('recipes/', views.RecipeListApi.as_view(), name='recipe-list'),
    path('recipes/create', views.RecipeCreateApi.as_view(), name='recipe-create'),
    path('recipes/<slug>/update',
         views.RecipeUpdateApi.as_view(), name='recipe-update'),
    path('recipes/<slug>', views.RecipeDetilApi.as_view(), name='recipe-detail'),
    path('recipes/<slug>/send-to-nozbe',
         views.RecipeSendIngredientsToNozbe.as_view(), name='recipe-send-to-nozbe'),
    path('recipes/group/<pk>/<slug>', views.GroupRecipeDetailApi.as_view(),
         name='group-recipe-detail'),
    path('recipes/<slug>/delete',
         views.RecipeDeleteApi.as_view(), name='recipe-delete'),

    path('tags/', views.TagListApi.as_view(), name='tag-list'),
    path('tags/create', views.TagCreateApi.as_view(), name='tag-create'),
    path('tags/<slug>', views.TagDetailApi.as_view(), name='tag-detail'),
    path('tags/<slug>/update', views.TagUpdateApi.as_view(), name='tag-update'),
    path('tags/<slug>/delete', views.TagDeleteApi.as_view(), name='tag-delete'),

    path('ingredients/', views.IngredientListApi.as_view(), name='ingredient-list'),
    path('ingredients/create', views.IngredientCreateApi.as_view(),
         name='ingredient-create'),
    path('ingredients/<slug>/update', views.IngredientUpdateApi.as_view(),
         name='ingredient-update'),
    path('ingredients/<slug>/delete', views.IngredientDeleteApi.as_view(),
         name='ingredient-delete'),
    path('ingredients/<slug>', views.IngredientDetailApi.as_view(),
         name='ingredient-detail'),

    path('available-units/', views.UnitListApi.as_view(),
         name='unit-list'),
    # path('tags/', views.TagListApi.as_view(), name='tag-list'),
    # path('tags/create', views.TagCreateApi.as_view(), name='tag-create'),
    # path('tags/<slug>/update', views.TagUpdateApi.as_view(),
    #      name='tag-update'),
    # path('ingredients/',
    #      views.IngredientListApi.as_view(), name='ingredient-list'),
    # path('ingredients/create',
    #      views.IngredientCreateApi.as_view(), name='ingredient-create'),
    # path('ingredients/<slug>',
    #      views.IngredientDetailApi.as_view(), name='ingredient-detail'),
    # path('ingredients/<slug>/update',
    #      views.IngredientUpdateApi.as_view(), name='ingredient-update'),



]
