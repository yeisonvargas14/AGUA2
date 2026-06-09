from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_router, name='dashboard'),
    path('rol-redirect/', views.rol_redirect, name='rol_redirect'),
    path('registro/', views.register_view, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.profile_view, name='profile'),
    
    # Password Reset
    path('recuperar-contrasena/', views.password_reset_request_view, name='password_reset'),
    path('recuperar-contrasena/verificar/', views.password_reset_verify_view, name='password_reset_verify'),
    path('recuperar-contrasena/confirmar/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('recuperar-contrasena/completado/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),
]
