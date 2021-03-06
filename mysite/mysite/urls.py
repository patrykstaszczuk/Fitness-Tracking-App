"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
import debug_toolbar

from mysite import views


app_name = 'mysite'

urlpatterns = [
    path('', views.api_root, name='api-root'),
    path('admin', admin.site.urls),
    path('account/', include('users.urls')),
    path('fitness/', include('health.urls')),
    path('meals-tracker/', include('meals_tracker.urls')),
    path('food/', include('recipe.urls')),
    path('strava-auth/', views.StravaCodeApiView.as_view(), name='strava-auth'),
    path('strava-connection-status/',
         views.StravaCheckStatusApi.as_view(), name='strava-status'),
    path('__debug__/', include(debug_toolbar.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
