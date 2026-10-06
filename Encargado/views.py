from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth import logout, update_session_auth_hash
from cundicents.decorators import group_required
from .models import VerUsuarios


@group_required("Encargado")
def inicio_encargado(request):
    return render(request, "inicio_e.html")


# ===== Sección Configuración: Actualizar Usuario =====
@group_required("Encargado")
def actualizar_usuario(request):
    user = request.user
    user_id = user.id

    if request.method == 'POST':
        nombre    = request.POST.get('nombre', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        cedula    = request.POST.get('cedula', '').strip()
        correo    = request.POST.get('correo', '').strip()
        password  = request.POST.get('password', '').strip()

        # Si el campo password viene vacío, pasamos None al SP para no modificarla
        passw_para_sp = None
        if password:
            from django.contrib.auth.hashers import make_password
            passw_para_sp = make_password(password)

        try:
            with connection.cursor() as cursor:
                cursor.callproc('actualizar_Usuario', [user_id, nombre, apellidos, cedula, correo, passw_para_sp])

            # Si se proporcionó nueva contraseña, se actualiza el objeto de usuario y la sesión activa
            if password:
                user.set_password(password)
                user.save()
                update_session_auth_hash(request, user)

            messages.success(request, 'Datos actualizados correctamente.')
            return redirect('Actualizar-Usuario-E')

        except Exception as e:
            messages.error(request, f'Ocurrió un error al actualizar los datos: {e}')

    # Carga de datos del usuario
    try:
        usuario = VerUsuarios.objects.get(id=user_id)
    except VerUsuarios.DoesNotExist:
        usuario = None
        messages.error(request, "No se encontró el registro del usuario.")

    return render(request, 'configuracion_e.html', {'usuario': usuario})


# ===== Cerrar Sesión =====
@group_required("Encargado")
def cerrar_sesion(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')




