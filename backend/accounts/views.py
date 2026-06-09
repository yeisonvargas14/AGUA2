from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django import forms
from .models import User, PasswordResetCode
from .forms import (
    ClientRegisterForm,
    TelefonoAuthenticationForm,
    PasswordResetRequestForm,
    PasswordResetVerifyForm,
    SetNewPasswordForm,
)
from .utils import send_whatsapp_code
from orders.models import Cart
from orders.cart_helpers import transfer_cart


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = ClientRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Roles.CLIENT
            user.set_password(form.cleaned_data['password'])
            user.save()

            Cart.objects.get_or_create(user=user)
            transfer_cart(request, user)

            login(request, user)
            messages.success(request, f"¡Bienvenido a Agua de Mesa Santiago, {user.first_name}! Tu cuenta ha sido creada.")
            return redirect('client_dashboard')
        else:
            messages.error(request, "Error en el registro. Por favor verifica los datos.")
    else:
        form = ClientRegisterForm()
    return render(request, 'auth/register.html', {'form': form})


class CustomLoginView(DjangoLoginView):
    template_name = 'auth/login.html'
    authentication_form = TelefonoAuthenticationForm

    def form_valid(self, form):
        rol_solicitado = self.request.POST.get('rol', '')
        user = form.get_user()
        role_map = {
            'admin': User.Roles.ADMIN,
            'agency': User.Roles.AGENCY,
        }
        if rol_solicitado:
            is_valid_superuser = (rol_solicitado == 'admin' and user.is_superuser)
            if not is_valid_superuser and user.role != role_map.get(rol_solicitado):
                form.add_error(None, f"Esta cuenta no tiene el rol de {'Administrador' if rol_solicitado == 'admin' else 'Agencia'}.")
                return self.form_invalid(form)
        transfer_cart(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user
        messages.success(self.request, f"¡Hola de nuevo, {user.first_name or user.username or user.telefono}!")
        return reverse('rol_redirect')


def password_reset_request_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            telefono = form.cleaned_data['telefono']
            user = User.objects.get(telefono=telefono)
            codigo = ''.join(__import__('random').choices('0123456789', k=6))
            expira_en = timezone.now() + timedelta(minutes=10)
            reset_code = PasswordResetCode.objects.create(
                user=user,
                telefono=telefono,
                codigo=codigo,
                expira_en=expira_en
            )
            send_whatsapp_code(telefono, codigo)
            request.session['password_reset_code_id'] = reset_code.id
            messages.success(request, 'Se ha enviado un código de recuperación por WhatsApp.')
            return redirect('password_reset_verify')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'auth/password_reset.html', {'form': form})


def password_reset_verify_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    reset_code_id = request.session.get('password_reset_code_id')
    if not reset_code_id:
        return redirect('password_reset')
    reset_code = get_object_or_404(PasswordResetCode, pk=reset_code_id)
    if request.method == 'POST':
        form = PasswordResetVerifyForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo'].strip()
            if reset_code.codigo == codigo and reset_code.is_valid():
                request.session['password_reset_user_id'] = reset_code.user_id
                return redirect('password_reset_confirm')
            form.add_error('codigo', 'Código incorrecto o expirado.')
    else:
        form = PasswordResetVerifyForm()
    return render(request, 'auth/password_reset_verify.html', {'form': form})


def password_reset_confirm_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    user_id = request.session.get('password_reset_user_id')
    reset_code_id = request.session.get('password_reset_code_id')
    if not user_id or not reset_code_id:
        return redirect('password_reset')
    reset_code = get_object_or_404(PasswordResetCode, pk=reset_code_id)
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            if not reset_code.is_valid():
                form.add_error(None, 'El código ya no es válido. Solicita uno nuevo.')
            else:
                user = get_object_or_404(User, pk=user_id)
                user.set_password(form.cleaned_data['password'])
                user.save()
                reset_code.usado = True
                reset_code.save()
                request.session.pop('password_reset_user_id', None)
                request.session.pop('password_reset_code_id', None)
                messages.success(request, 'Tu contraseña se ha restablecido correctamente.')
                return redirect('password_reset_complete')
    else:
        form = SetNewPasswordForm()
    return render(request, 'auth/password_reset_confirm.html', {'form': form})


@login_required
def rol_redirect(request):
    """Central redirect after login based on role and agency status."""
    user = request.user
    if user.role == User.Roles.ADMIN or user.is_superuser:
        return redirect('admin_dashboard')
    elif user.role == User.Roles.AGENCY:
        try:
            agency = user.agencia
            if not agency.activa:
                from django.contrib.auth import logout
                logout(request)
                messages.error(request, "Su cuenta está desactivada. Contacte al administrador.")
                return redirect('login')
        except Exception:
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, "No tienes una agencia asignada. Contacta al administrador.")
            return redirect('login')
        return redirect('agency_dashboard')
    elif user.role == User.Roles.DRIVER:
        return redirect('driver_dashboard')
    else:
        return redirect('client_dashboard')

def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect('login')

@login_required
def dashboard_router(request):
    """
    Routes user to the appropriate home page based on role.
    """
    user = request.user
    if user.role == User.Roles.ADMIN:
        return redirect('admin_dashboard')
    elif user.role == User.Roles.AGENCY:
        return redirect('agency_dashboard')
    elif user.role == User.Roles.DRIVER:
        return redirect('driver_dashboard')
    else:
        return redirect('client_dashboard')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telefono', 'address', 'municipio', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'municipio': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('profile')
        else:
            messages.error(request, "Error al actualizar perfil.")
    else:
        form = ProfileForm(instance=user)
    return render(request, 'auth/profile.html', {'form': form})
