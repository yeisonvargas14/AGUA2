from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from products import views as products_views
from core import views as core_views
from orders import views as orders_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Landing Page
    path('', products_views.landing_page, name='landing'),
    path('api/validate-location/', orders_views.validate_location, name='api_validate_location'),
    
    # Auth & Accounts
    path('', include('accounts.urls')),
    
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
    
    # Client Panel & Public Catalogue
    path('catalogo/', include('products.urls')),
    path('pedidos/', include('orders.urls')),
    
    # Agency Panel
    path('agencia/', include('agencies.urls')),
    
    # Driver Panel
    path('repartidor/', include('distribution.urls')),
    
    # Seller Panel
    path('vendedor/', include('vendedor.urls')),
    
    # Admin Panel
    path('administrador/', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
