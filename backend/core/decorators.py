from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*roles):
    """
    Decorator that checks if the logged-in user has one of the specified roles.
    If the user is not authenticated, redirects to 'login'.
    If the user does not have the correct role, redirects to their corresponding role home dashboard.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.role not in roles:
                messages.error(request, "No tienes permiso para acceder a esta sección.")
                if request.user.role == 'admin':
                    return redirect('admin_dashboard')
                elif request.user.role == 'agency':
                    return redirect('agency_dashboard')
                elif request.user.role == 'driver':
                    return redirect('driver_dashboard')
                else:
                    return redirect('client_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

