from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalogo_view, name='client_dashboard'), # client home is the product catalog
    path('<int:pk>/', views.product_detail_view, name='product_detail'),
]
