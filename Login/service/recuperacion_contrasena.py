from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import secrets


def generar_codigo(longitud: int = 6) -> str:
    numero = secrets.randbelow(10 ** longitud)
    return str(numero).zfill(longitud)

# ============================================================
#  CORREO DE RECUPERACIÓN DE CONTRASEÑA
# ============================================================
def enviar_codigo(correo, destinatario, minutos_expiracion):
    codigo = generar_codigo()
    contexto = {'nombre': destinatario, 'codigo': codigo, 'minutos': minutos_expiracion}
    html_content = render_to_string('recuperacion_contrasena_mensaje.html', contexto)

    send_mail(
        subject='Código de recuperación · Sistema de Incidentes',
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[correo],
        html_message=html_content,
        fail_silently=False,
    )
    return codigo
