from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views

router = DefaultRouter()
router.register('skladniki', views.IngredientViewSet)
router.register('tagi', views.TagViewSet)
router.register('przepisy', views.RecipeViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
    path('przepisy/<pk>/<slug>', views.RecipeDetailViewSet.
         as_view({'get': 'retrieve'}), name='recipe-group-detail'),
    path('dostepne-jednostki/', views.UnitViewSet.as_view({'get': 'list'}),
         name='units'),
]
