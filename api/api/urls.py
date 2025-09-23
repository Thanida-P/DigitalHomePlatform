"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path
import app_api.users.view as user_views

urlpatterns = [
    path('users/admin/register/', user_views.register_admin),
    path('users/login/', user_views.login_view),
    path('users/register/', user_views.register),
    path('users/logout/', user_views.logout_view),
    path('users/is_logged_in/', user_views.is_logged_in),
]
