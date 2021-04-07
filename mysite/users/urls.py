from django.urls import path

from users import views

app_name = 'users'

urlpatterns = [
    path('nowy_uzytkownik/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('informacje/', views.ManageUserView.as_view(), name='profile'),
    path('nowe_haslo/', views.ChangeUserPasswordView.as_view(),
         name='password_change')
]
