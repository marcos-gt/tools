from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('cadastro/', views.signup, name='signup'),
    path('cadastro/enviado/', views.signup_done, name='signup_done'),
    path('confirmar-email/<str:uidb64>/<str:token>/', views.activate_account, name='activate_account'),
    path('confirmado/', views.activation_done, name='activation_done'),
    path('reenviar-confirmacao/', views.resend_confirmation, name='resend_confirmation'),
    path('reenviar-confirmacao/enviado/', views.resend_done, name='resend_done'),
    path('recuperar-senha/', views.RecoveryView.as_view(), name='password_reset'),
    path('recuperar-senha/enviado/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('redefinir-senha/<str:uidb64>/<str:token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('senha-redefinida/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('logout/', views.logout_view, name='logout'),
    ]
