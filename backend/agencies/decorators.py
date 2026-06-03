from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from functools import wraps


def agency_active_required(view_func):
    """
    Decorator that ensures the user is authenticated, has role 'agency',
    and their Agency profile is active. If inactive, logs out and redirects to login.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if user.role != 'agency':
            messages.error(request, "No tienes permiso para acceder a esta sección.")
            return redirect('login')
        try:
            agency = user.agencia
        except Exception:
            messages.error(request, "No tienes una agencia asignada. Contacta al administrador.")
            return redirect('login')
        if not agency.activa:
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, "Su cuenta está desactivada. Contacte al administrador.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped
