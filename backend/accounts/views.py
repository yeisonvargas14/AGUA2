from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from .models import User
from django import forms
from orders.models import Cart
from orders.cart_helpers import transfer_cart

class ClientRegisterForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=250,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Completo'}),
        label="Nombre Completo"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
        label="Contraseña"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar Contraseña'}),
        label="Confirmar Contraseña"
    )

    class Meta:
        model = User
        fields = ['email', 'phone', 'address', 'municipio']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Celular'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'municipio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Municipio (ej: Comarapa)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'phone' in self.fields:
            self.fields['phone'].label = 'Celular'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password != password_confirm:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name', '').strip()
        
        # Split full name into first_name and last_name
        parts = full_name.split(' ', 1)
        if len(parts) > 1:
            user.first_name = parts[0]
            user.last_name = parts[1]
        else:
            user.first_name = full_name
            user.last_name = ''
            
        # Set username to match email (or random, or email username) to satisfy unique/non-null constraints if any,
        # but since USERNAME_FIELD is 'email', we can just use the email prefix or the email itself
        user.username = user.email

        if commit:
            user.save()
        return user

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
            
            # Ensure client has a persistent cart
            Cart.objects.get_or_create(user=user)
            
            # Merge any anonymous cart into the new user's cart
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

    def form_valid(self, form):
        """Check that the role button used matches the user's actual role."""
        rol_solicitado = self.request.POST.get('rol', '')  # 'admin', 'agency', or ''
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
        # Merge anonymous cart before calling super() which calls login()
        transfer_cart(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user
        messages.success(self.request, f"¡Hola de nuevo, {user.first_name or user.username}!")
        return reverse('rol_redirect')


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
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'municipio', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
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
