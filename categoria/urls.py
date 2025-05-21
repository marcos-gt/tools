from django.urls import path
from . import views

urlpatterns = [
    path('', views.categoria, name='categoria'),
]