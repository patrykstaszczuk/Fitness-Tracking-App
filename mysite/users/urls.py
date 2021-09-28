from django.urls import path, include
from users import views
from rest_framework.routers import DefaultRouter

# router = DefaultRouter()
# router.register('', views.GroupViewSet, basename='group')
app_name = 'users'

urlpatterns = [
    path('new-user/', views.UserCreateApi.as_view(), name='user-create'),
    path('token/', views.ObtainTokenView.as_view(), name='user-token'),
    path('profile/', views.UserProfileApi.as_view(), name='user-profile'),
    path('update/', views.UserUpdateApi.as_view(), name='user-update'),
    path('new-password/', views.UserChangePasswordApi.as_view(),
         name='user-change-password'),
    path('groups/', views.UserListGroupApi.as_view(), name='user-group'),
    path('groups/send-invitation', views.UserSendGroupInvitationApi.as_view(),
         name='user-send-group-invitation'),
    path('groups/accept-invitations', views.UserAcceptInvitationApi.as_view(),
         name='user-accept-group-invitation'),
    path('groups/deny-invitations', views.UserDenyInvitationApi.as_view(),
         name='user-deny-group-invitation'),
     path('groups/leave-group', views.UserLeaveGroupApi.as_view(),
          name='user-leave-group')
    # path('groups/', include(router.urls)),
]
