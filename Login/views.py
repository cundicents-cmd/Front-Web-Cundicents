import json, hmac, re
from .service.recuperacion_contrasena import enviar_codigo
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, DatabaseError
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import VerUsuarios
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse


def login_view(request):
    error = None
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        if not User.objects.filter(username=email).exists():
            error = "El usuario no existe."
        else:
            # El usuario existe, ahora verificamos la contraseña
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                grupos_usuario = list(user.groups.values_list("name", flat=True))
                if not grupos_usuario:
                    error = "No perteneces a ningún grupo válido."
                    return redirect("Login")
                grupo = grupos_usuario[0]
                match grupo:
                    case "Gubernamental":
                        return redirect("Gobernacion")
                    case "Municipal":
                        return redirect("Municipalidad")
                    case "Encargado":
                        return redirect("Encargado")
                    case _:
                        error = "No perteneces a un grupo válido."
                        return redirect("Login")
            else:
                error = "La contraseña es incorrecta."
    
    return render(request, "index.html", {"error": error})

@login_required
def logout_g(request):
    logout(request)
    return redirect("Login")

def error_403(request):
    return render(request, "403.html")

def error_404(request):
    return render(request, "404.html")

#Recuperacion de contraseña
def recuperar_contrasena(request):
    return render(request, "recuperacion_contrasena.html")

@require_POST
def enviar_codigo_recuperacion(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        return JsonResponse({'success': False, 'message': f'Ocurrió un error: {e}'}, status=400)

    correo = (data.get('correo') or '').strip().lower()
    if not correo:
        return JsonResponse({'success': False, 'message': 'Debes ingresar un correo.'}, status=400)

    if not VerUsuarios.objects.filter(correo=correo).exists():
        return JsonResponse(
            {'success': False, 'message': f'El correo {correo} no está registrado.'},
            status=400
        )

    usuario = VerUsuarios.objects.get(correo=correo)
    try:
        codigo = enviar_codigo(correo, f"{usuario.nombre} {usuario.apellidos}", 5)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {e}'}, status=500)


    request.session['recuperacion_correo'] = correo
    request.session['recuperacion_codigo'] = codigo
    request.session['recuperacion_expira'] = (timezone.now() + timedelta(minutes=5)).isoformat()
    request.session['recuperacion_verificado'] = False

    return JsonResponse({'success': True, 'message': 'Código enviado. Revisa tu bandeja de entrada y spam.'})

@require_POST
def verificar_codigo_recuperacion(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Datos inválidos.'}, status=400)

    codigo_ingresado = (data.get('codigo') or '').strip()

    if not codigo_ingresado.isdigit() or len(codigo_ingresado) != 6:
        return JsonResponse(
            {'success': False, 'message': 'El código debe tener 6 dígitos.'},
            status=400
        )

    codigo_guardado = request.session.get('recuperacion_codigo')
    expira_str      = request.session.get('recuperacion_expira')
    correo          = request.session.get('recuperacion_correo')

    if not (codigo_guardado and expira_str and correo):
        return JsonResponse(
            {'success': False, 'message': 'No hay una solicitud de recuperación activa.'},
            status=400
        )

    try:
        expira = datetime.fromisoformat(expira_str)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'Datos de sesión inválidos.'}, status=400)

    if timezone.now() > expira:
        _limpiar_sesion_recuperacion(request)
        return JsonResponse(
            {'success': False, 'message': 'El código ha expirado. Solicita uno nuevo.'},
            status=400
        )

    if not hmac.compare_digest(str(codigo_guardado), str(codigo_ingresado)):
        return JsonResponse(
            {'success': False, 'message': 'El código ingresado es incorrecto.'},
            status=400
        )

    request.session['recuperacion_verificado'] = True
    return JsonResponse({
        'success': True,
        'message': 'Código verificado. Ahora crea tu nueva contraseña.'
    })

@require_POST
def actualizar_contrasena(request):
    if not request.session.get('recuperacion_verificado'):
        return JsonResponse({'success': False, 'message': 'Debes verificar el código primero.'})

    correo = request.session.get('recuperacion_correo')
    if not correo:
        _limpiar_sesion_recuperacion(request)
        return JsonResponse({'success': False, 'message': 'La sesión de recuperación expiró.'}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Datos inválidos.'}, status=400)

    password  = data.get('password')  or ''
    confirmar = data.get('confirmar') or ''

    if password != confirmar:
        return JsonResponse({'success': False, 'message': 'Las contraseñas no coinciden.'}, status=400)

    es_valida, msg = validar_password_segura(password)
    if not es_valida:
        return JsonResponse({'success': False, 'message': msg}, status=400)

    try:
        with connection.cursor() as cursor:
            has_pass = make_password(password)
            cursor.callproc('sp_actualizar_password', [correo, has_pass])
    except DatabaseError as e:
        return JsonResponse({'success': False, 'message': f'Error en base de datos: {e}'}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error inesperado: {e}'}, status=500)

    _limpiar_sesion_recuperacion(request)

    mensaje = "Contraseña actualizada exitosamente. Ya puedes iniciar sesión."

    # Guarda el mensaje para que lo pinte la página de Login al llegar.
    messages.success(request, mensaje)

    return JsonResponse({
        'success': True,
        'message': mensaje,
        'redirect': reverse('Login'),
    })

# ============================================================
# Helpers
# ============================================================
def _limpiar_sesion_recuperacion(request):
    for k in (
        'recuperacion_correo',
        'recuperacion_codigo',
        'recuperacion_expira',
        'recuperacion_verificado',
    ):
        request.session.pop(k, None)  

SPECIAL_CHARS_RE = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`]")
def validar_password_segura(pwd: str) -> tuple[bool, str]:
    """Devuelve (es_valida, mensaje_de_error)."""
    if not pwd:
        return False, 'La contraseña no puede estar vacía.'
    if len(pwd) < 8:
        return False, 'La contraseña debe tener mínimo 8 caracteres.'
    if len(pwd) > 64:
        return False, 'La contraseña no puede superar los 64 caracteres.'
    if not re.search(r'[a-z]', pwd):
        return False, 'Debe incluir al menos una letra minúscula.'
    if not re.search(r'[A-Z]', pwd):
        return False, 'Debe incluir al menos una letra mayúscula.'
    if not re.search(r'[0-9]', pwd):
        return False, 'Debe incluir al menos un número (0-9).'
    if not SPECIAL_CHARS_RE.search(pwd):
        return False, 'Debe incluir al menos un símbolo especial (!@#$%...).'
    return True, ''
          