from django.urls import path, include
from web.auth import api_login
from . import views

urlpatterns = [
    # path('login/', include('django.contrib.auth.urls')),  # Default auth URLs
    path('', views.login,name='login'),
    path('logout/', views.logout_view, name='logout'),
    ]