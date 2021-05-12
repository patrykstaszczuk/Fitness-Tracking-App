from django.urls import path, include
from users import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', views.GroupViewSet)
app_name = 'users'

urlpatterns = [
    path('nowy_uzytkownik/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('informacje/', views.ManageUserView.as_view(), name='profile'),
    path('nowe_haslo/', views.ChangeUserPasswordView.as_view(),
         name='password_change'),
    path('grupa/', include(router.urls)),
]
