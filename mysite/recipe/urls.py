from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views

router = DefaultRouter()
router.register('skladniki', views.IngredientViewSet)
router.register('tagi', views.TagViewSet)
router.register('przepisy', views.RecipeViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
