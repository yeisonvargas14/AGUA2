from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class TelefonoBackend(ModelBackend):
    """Autentica usuarios usando el campo telefono en lugar de username o email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        telefono = username or kwargs.get('telefono')
        if telefono is None or password is None:
            return None
        try:
            user = UserModel.objects.get(telefono=telefono)
        except UserModel.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
