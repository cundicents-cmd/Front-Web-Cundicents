from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import VerMunicipios, VerUsuarios
from django.db import connection
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from cundicents.decorators import group_required
from django.contrib import messages
from django.views.decorators.http import require_POST


@login_required
@group_required("Gubernamental")
def inicio_gubernamental(request):
    #granjas = VerGranjas.objects.all()
    #context = {"granjas": granjas,}
    return render(request, "inicio_g.html")

# ==========================================================
# Views de la seccion de gestion de municipios
# ==========================================================
@login_required
@group_required("Gubernamental")
def gestion_municipios(request):
    municipios = VerMunicipios.objects.all()
    return render(request, 'municipios_g.html', {'municipios': municipios})

@login_required
@group_required("Gubernamental")
def agregar_municipio(request):
    nombre = request.POST.get('nombre', '').strip()
    try:
        with connection.cursor() as cursor:
            cursor.callproc('agregar_Municipio', [nombre])
        return JsonResponse({'ok': True, 'tipo': 'municipio_creado', 'mensaje': 'Municipio agregado correctamente.'})
    except Exception as e:
        return JsonResponse({'ok': False, 'tipo': 'municipio_error', 'mensaje': 'Ocurrió un error al crear el municipio.', 'error': str(e)}, status=500)

@login_required
@group_required("Gubernamental")
def eliminar_municipio(request):
    if request.method == 'POST':
        id_municipio = request.POST.get('id_municipio', '').strip()
        try:
            with connection.cursor() as cursor:
                cursor.execute( "CALL eliminar_Municipio(%s, @p_mensaje);", [id_municipio])
                cursor.execute("SELECT @p_mensaje;")
                fila = cursor.fetchone()
                mensaje_sp = fila[0] if fila else None

            if mensaje_sp == 'Municipio eliminado correctamente':
                return JsonResponse({'ok': True, 'tipo': 'municipio_eliminado', 'mensaje': 'Municipio eliminado correctamente.'})
            else:
                return JsonResponse({'ok': False, 'tipo': 'municipio_error', 'mensaje': mensaje_sp or 'Error al eliminar el municipio.', 'error': mensaje_sp or 'Error al eliminar el municipio' }, status=400)

        except Exception as e:
            return JsonResponse({'ok': False, 'tipo': 'municipio_error', 'mensaje': 'Ocurrió un error al eliminar el municipio.', 'error': f'Error: {str(e)}'}, status=500)


# ==========================================================
# Views de gestion de administradores
# ==========================================================
@login_required
@group_required("Gubernamental")
def agregar_administrador(request):
    id = request.GET.get('id_municipio', '').strip()
    if not id:
        return redirect('Municipios')
    contexto = {'id_municipio': id}
    return render(request, 'agregar_administrador_g.html', contexto)

@login_required
@group_required("Gubernamental")
def registrar_administrador(request):
    id_municipio = request.GET.get('id_municipio', '').strip()
    if request.method == 'POST':
        id_municipio = request.POST.get('id_municipio', id_municipio).strip()

    if not id_municipio:
        return redirect('Municipios')

    contexto = {'id_municipio': id_municipio}

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        cedula = request.POST.get('cedula', '').strip()
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')
        password_hash = make_password(password)

        mensaje_sp = ''
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "CALL registrar_Administrador_Municipio(%s, %s, %s, %s, %s, %s, @p_mensaje)",
                    [nombre, apellidos, correo, password_hash, cedula, int(id_municipio)]
                )
                cursor.execute("SELECT @p_mensaje")
                fila = cursor.fetchone()
                mensaje_sp = fila[0] if fila else ''

        except Exception as e:
            contexto['tipo'] = 'administrador_error'
            contexto['mensaje_ui'] = f'⚠️ Error al registrar: {e}'
            messages.error(request, f'⚠️ Error al registrar: {e}')
            return render(request, 'agregar_administrador_g.html', contexto)

        if mensaje_sp != "Usuario registrado correctamente":
            contexto['tipo'] = 'administrador_error'
            contexto['mensaje_ui'] = f'⚠️ {mensaje_sp or "No se recibió respuesta del servidor."}'
            messages.error(request, f'⚠️ {mensaje_sp or "No se recibió respuesta del servidor."}')
            return render(request, 'agregar_administrador_g.html', contexto)
        else:
            messages.success(request, '✅ Administrador agregado exitosamente.')
            return redirect('Municipios')

    return render(request, 'agregar_administrador_g.html', contexto)

@login_required
@group_required("Gubernamental")
@require_POST
def eliminar_administrador(request):
    id_usuario = request.POST.get('id_usuario')
    try:
        with connection.cursor() as cursor:
            cursor.callproc('eliminar_Administrador', [id_usuario])
        return JsonResponse({
            'ok': True, 'tipo': 'administrador_eliminado', 'mensaje': 'Administrador eliminado correctamente.'})
    except Exception as e:
        return JsonResponse({'ok': False, 'tipo': 'administrador_error', 'mensaje': 'Ocurrió un error al eliminar el administrador.', 'error': str(e)}, status=500)

@login_required
@group_required("Gubernamental")
def actualizar_administrador(request, id):
    # ===== Obtener el administrador =====
    try:
        administrador = VerUsuarios.objects.get(id=id)
    except VerUsuarios.DoesNotExist:
        messages.error(request, 'El administrador no existe.')
        return redirect('Municipios')

    # ===== GET: mostrar formulario con datos actuales =====
    if request.method != 'POST':
        return render(request, 'actualizar_administrador_g.html', {
            'administrador': administrador
        })

    nombre    = request.POST.get('nombre', '').strip()
    apellidos = request.POST.get('apellidos', '').strip()
    cedula    = request.POST.get('cedula', '').strip()
    correo    = request.POST.get('correo', '').strip()
    password  = request.POST.get('password', '').strip()


    # ----- Validar cédula duplicada (otro usuario) -----
    if VerUsuarios.objects.filter(cedula=cedula).exclude(id=id).exists():
        messages.error(request, 'La cédula ya está registrada por otro usuario.')
        return render(request, 'actualizar_administrador_g.html', {
            'administrador': administrador
        })

    # ----- Validar correo duplicado (otro usuario) -----
    if VerUsuarios.objects.filter(correo=correo).exclude(id=id).exists():
        messages.error(request, 'El correo ya está registrado por otro usuario.')
        return render(request, 'actualizar_administrador_g.html', {
            'administrador': administrador
        })

    # ----- Guardar cambios -----
    try:
        with connection.cursor() as cursor:
            cursor.callproc('actualizar_Usuario', [id , nombre, apellidos, cedula, correo, make_password(password)])
        messages.success(request, 'Administrador actualizado correctamente.')
        return redirect('Municipios')

    except Exception as e:
        # ❌ Error → se queda en HTML2 con el mensaje
        messages.error(request, f'Ocurrió un error al actualizar el administrador: {e}')
        return render(request, 'actualizar_administrador_g.html', {
            'administrador': administrador
        })
      