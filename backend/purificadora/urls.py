"""
URL configuration for purificadora project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='base.html'), name='home'),
    
    # API endpoints
    path('api/seed/', core_views.seed_data, name='api_seed'),
    path('api/stats/', core_views.api_dashboard_stats, name='api_stats'),
    path('api/products/', core_views.api_products, name='api_products'),
    path('api/products/<int:pk>/', core_views.api_product_detail, name='api_product_detail'),
    path('api/orders/', core_views.api_orders, name='api_orders'),
    path('api/orders/<int:pk>/status/', core_views.api_order_status, name='api_order_status'),
    path('api/agencies/', core_views.api_agencies, name='api_agencies'),
    path('api/inventory/', core_views.api_inventory, name='api_inventory'),
    path('api/deliveries/', core_views.api_deliveries, name='api_deliveries'),
]


