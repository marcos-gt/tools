from django.urls import path
from . import views

urlpatterns = [
    path('usuario/view', views.home, name='home'),  # Exemplo de view
    path('usuario/save', views.user_create, name='user_create'),  # formulário
]