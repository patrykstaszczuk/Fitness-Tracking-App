from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views

router = DefaultRouter()
router.register('ingredients', views.IngredientViewSet)
router.register('tags', views.TagViewSet)
router.register('recipes', views.RecipeViewSet, basename='recipe')

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
    path('available-units/', views.UnitViewSet.as_view({'get': 'list'}),
         name='units'),
]
