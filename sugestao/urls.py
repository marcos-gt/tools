from django.urls import path
from . import views

urlpatterns = [
    path('', views.sugestao, name='sugestao'),
]