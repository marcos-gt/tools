from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat, name='chat'),
    path('meus/', views.meus_chats, name='meus'),
    path('novo/', views.novo_chat, name='novo_chat'),
    path('inativar/', views.inativar_chats, name='inativar_chats'),

]