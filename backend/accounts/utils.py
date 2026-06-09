import os
from django.conf import settings

try:
    from twilio.rest import Client
except ImportError:
    Client = None


def send_whatsapp_code(telefono: str, codigo: str) -> None:
    mensaje = f"Tu código de recuperación de AquaFlow es: {codigo}"
    from_number = settings.TWILIO_WHATSAPP_FROM
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN

    if all([account_sid, auth_token, from_number]) and Client:
        try:
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=mensaje,
                from_=f"whatsapp:{from_number}",
                to=f"whatsapp:{telefono}"
            )
            return
        except Exception as exc:
            print(f"[WhatsApp Twilio error] {exc}")

    print(f"[WhatsApp simulado] Enviar a {telefono}: {mensaje}")
