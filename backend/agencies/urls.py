from django.urls import path
from . import views

urlpatterns = [
    path('', views.agency_dashboard, name='agency_dashboard'),
    path('crear-pedido/', views.agency_create_order, name='agency_create_order'),
]
