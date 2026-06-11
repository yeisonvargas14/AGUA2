import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

PHONE_REGEX = re.compile(r'^\+?\d{7,15}$')

class ClientRegisterForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de Usuario'}),
        label="Usuario"
    )
    full_name = forms.CharField(
        max_length=250,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Completo'}),
        label="Nombre Completo"
    )
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+591 7xxxxxxx'}),
        label="Celular (opcional)"
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'usuario@ejemplo.com'}),
        label="Correo Electrónico"
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
        fields = ['username', 'telefono', 'email', 'address', 'municipio']

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")
        return username

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if not telefono:
            return None
        telefono = telefono.replace(' ', '')
        if not PHONE_REGEX.match(telefono):
            raise forms.ValidationError("Ingresa un número de celular válido.")
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email', '').strip()
        user.email = email if email else None
        full_name = self.cleaned_data.get('full_name', '').strip()
        parts = full_name.split(' ', 1)
        if len(parts) > 1:
            user.first_name = parts[0]
            user.last_name = parts[1]
        else:
            user.first_name = full_name
            user.last_name = ''
        if commit:
            user.save()
        return user


class UsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'class': 'form-control',
            'placeholder': 'Usuario'
        }),
        label='Usuario'
    )


class PasswordResetRequestForm(forms.Form):
    telefono = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+591 7xxxxxxx'}),
        label='Celular'
    )

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if not PHONE_REGEX.match(telefono.replace(' ', '')):
            raise ValidationError("Ingresa un número de celular válido.")
        if not User.objects.filter(telefono=telefono).exists():
            raise ValidationError("No existe una cuenta registrada con ese número de celular.")
        return telefono


class PasswordResetVerifyForm(forms.Form):
    codigo = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código de 6 dígitos'}),
        label='Código'
    )


class SetNewPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nueva contraseña'}),
        label='Nueva Contraseña'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar contraseña'}),
        label='Confirmar Contraseña'
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Las contraseñas no coinciden.")
        return cleaned_data
