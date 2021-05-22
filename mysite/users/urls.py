from django.urls import path, include
from users import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', views.GroupViewSet)
app_name = 'users'

urlpatterns = [
    path('nowy-uzytkownik/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('informacje/', views.ManageUserView.as_view(), name='profile'),
    path('nowe-haslo/', views.ChangeUserPasswordView.as_view(),
         name='password-change'),
    path('grupa/', include(router.urls)),
]
