from django.urls import path
from users import views

app_name = 'users'

urlpatterns = [
    path('new-user/', views.CreateUserApi.as_view(), name='user-create'),
    path('token/', views.ObtainTokenView.as_view(), name='create-token'),
    path('profile/', views.UserProfileApi.as_view(), name='user-profile'),
    path('profile/update/', views.UpdateUserApi.as_view(), name='user-update'),
    path('profile/new_password', views.ChangeUserPasswordApi.as_view(),
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
]
