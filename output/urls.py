from django.urls import path
from . import views
urlpatterns = [path('', views.output, name='output'),
    path('<int:pk>/export/<str:format>/', views.export, name='export_output'),
    path('<int:pk>/render-status/', views.render_status, name='render_status')]
