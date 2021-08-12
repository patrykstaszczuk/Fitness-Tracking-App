from django.urls import path, include
from users import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', views.GroupViewSet)
app_name = 'users'

urlpatterns = [
    path('new-user/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('profile/', views.ManageUserView.as_view(), name='profile'),
    path('strava-code/', views.StravaCodeApiView.as_view(), name='strava-code'),
    path('new-password/', views.ChangeUserPasswordView.as_view(),
         name='password-change'),
    path('groups/', include(router.urls)),
]
