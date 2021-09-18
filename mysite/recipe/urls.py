from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views

router = DefaultRouter()
#router.register('ingredients', views.IngredientViewSet)
#router.register('tags', views.TagViewSet, basename='tag')
router.register('recipes', views.RecipeViewSet, basename='recipe')

app_name = 'recipe'


urlpatterns = [
    path('', include(router.urls)),
    path('available-units/', views.UnitViewSet.as_view(),
         name='units'),
    path('tags/', views.TagListApi.as_view(), name='tag-list'),
    path('tags/create', views.TagCreateApi.as_view(), name='tag-create'),
    path('tags/<slug>/update', views.TagUpdateApi.as_view(),
         name='tag-update'),
    path('ingredients/',
         views.IngredientListApi.as_view(), name='ingredient-list'),
    path('ingredients/create',
         views.IngredientCreateApi.as_view(), name='ingredient-create'),
    path('ingredients/<slug>',
         views.IngredientDetailApi.as_view(), name='ingredient-detail'),
    path('ingredients/<slug>/update',
         views.IngredientUpdateApi.as_view(), name='ingredient-update'),



]
