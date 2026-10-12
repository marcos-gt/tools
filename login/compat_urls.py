"""Mantém caminhos antigos passando pelos mesmos controles e origem de email."""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login),
    path('logout/', views.logout_view),
    path('password_reset/', views.RecoveryView.as_view()),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view()),
    path('reset/<str:uidb64>/<str:token>/', auth_views.PasswordResetConfirmView.as_view()),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view()),
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
]
