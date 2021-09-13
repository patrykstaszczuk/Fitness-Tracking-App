from django.urls import path, include
from users import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', views.GroupViewSet, basename='group')
app_name = 'users'

urlpatterns = [
    path('new-user/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('profile/', views.ManageUserView.as_view(), name='profile'),
    path('new-password/', views.ChangeUserPasswordView.as_view(),
         name='password-change'),
    path('groups/', include(router.urls)),
]
