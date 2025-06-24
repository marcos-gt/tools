"""
URL configuration for web project.

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
from django.urls import path, include
from web.auth import api_login


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('chat/', include('chat.urls')),
    path('output/', include('output.urls')),
    path('categoria/', include('categoria.urls')),
    path('sugestao/', include('sugestao.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api-login/', api_login, name='api_login'),
    path('login/',include('login.urls'), name='login'),
    path('logout/', include('django.contrib.auth.urls')),

]
