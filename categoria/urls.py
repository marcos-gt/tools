from django.urls import path
from . import views

urlpatterns = [
    path('', views.categoria, name='categoria'),
    path('lista/', views.list_all, name='lista_categorias'),
    path ('renderizar/', views.renderizar, name='renderizar_categoria'),
    path('receberCategorias/', views.receberCategorias, name='receber_categorias'),
]