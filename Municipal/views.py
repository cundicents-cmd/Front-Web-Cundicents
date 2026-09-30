import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from .models import verUsuariosResponsabilidades, ver_Usuario_Municipio_Responsabilidad, verSectores, VerUsuarios
from cundicents.decorators import group_required


def puntos_a_wkt(puntos):
    coords = [(p[1], p[0]) for p in puntos] 
    if coords[0] != coords[-1]:
        coords.append(coords[0])           
    anillo = ", ".join(f"{lng} {lat}" for lng, lat in coords)
    return f"POLYGON(({anillo}))"

@group_required("Municipal")
def inicio_municipalidad(request):
    #granjas = VerGranjas.objects.all()
    #context = {"granjas": granjas,}
    return render(request, "inicio_m.html")


#Views de la gestion de sectores
@group_required("Municipal")
def gestion_sectores(request):
    id_user = request.user.id
    id_Municipio = ver_Usuario_Municipio_Responsabilidad.objects.get(id_usuario=id_user).id_municipio
    sectores = verSectores.objects.filter(id_municipio=id_Municipio)
    return render(request, "sectores_m.html", {"sectores": sectores})

@group_required("Municipal")
def crear_sector(request):
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        puntos_raw = request.POST.get('puntos') or '[]'

        if not nombre:
            messages.error(request, 'El nombre del sector es obligatorio.')
            return redirect('Crear-Sector')

        try:
            puntos = json.loads(puntos_raw)
        except json.JSONDecodeError:
            messages.error(request, 'Los puntos del sector no son válidos.')
            return redirect('Crear-Sector')

        if not isinstance(puntos, list) or len(puntos) < 4:
            messages.error(request, 'Debes dibujar al menos 4 puntos y cerrar el sector.')
            return redirect('Crear-Sector')

        # Convertir a WKT para MySQL
        try:
            wkt = puntos_a_wkt(puntos)
        except ValueError as e:
            return redirect('Crear-Sector')

        # Obtener municipio del usuario
        
        id_municipio = ver_Usuario_Municipio_Responsabilidad.objects.get(id_usuario=request.user.id).id_municipio
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "CALL agregar_Sector(%s, %s, %s, @p_mensaje)",
                    [id_municipio, nombre, wkt]
                )
                cursor.execute("SELECT @p_mensaje")
                fila = cursor.fetchone()
                mensaje_sp = fila[0] if fila else ''
        except Exception as e:
            messages.error(request, f'Error al guardar el sector: {e}')
            return redirect('Crear-Sector')
        if mensaje_sp != "Sector registrado correctamente.": 
            messages.success(request, f'Error: "{mensaje_sp}".')
            return redirect('Sectores')
        else:
            messages.success(request, f'Sector "{nombre}" guardado correctamente.')
            return redirect('Sectores')

    return render(request, "crear_sector.html")

@group_required("Municipal")
def ver_sector(request, sector_id):
    sector = get_object_or_404(verSectores, id=sector_id)
    return render(request, 'ver_sector_m.html', {'sector': sector})

@group_required("Municipal")
def eliminar_sector(request, sector_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "CALL eliminar_Sector(%s, @p_mensaje)",
                [sector_id]
            )
            cursor.execute("SELECT @p_mensaje")
            fila = cursor.fetchone()
            mensaje_sp = fila[0] if fila else ''
    except Exception as e:
        messages.error(request, f'Error al eliminar el sector: {e}')
        return redirect('Sectores')
    if mensaje_sp != "Sector eliminado correctamente.": 
        messages.success(request, f'Error: "{mensaje_sp}".')
        return redirect('Sectores')
    else:
        messages.success(request, f'{mensaje_sp}')
        return redirect('Sectores')


#Views de la gestion de encargados
@group_required("Municipal")
def gestion_encargados(request):
    id_municipio = ver_Usuario_Municipio_Responsabilidad.objects.get(id_usuario=request.user.id).id_municipio
    encargados_SyC = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=1)    
    encargados_Ac = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=2)
    encargados_GdR = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=3)
    encargados_I = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=4)
    encargados_SePu = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=5)
    encargados_Am = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=6)
    encargados_SaPu = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=7)
    context = {
        'id_municipio':   id_municipio,
        'encargados_SyC':  encargados_SyC,
        'encargados_Ac':   encargados_Ac,
        'encargados_GdR':  encargados_GdR,
        'encargados_I':    encargados_I,
        'encargados_SePu': encargados_SePu,
        'encargados_Am':   encargados_Am,
        'encargados_SaPu': encargados_SaPu,
    }
    return render(request, 'encargados_m.html', context)


@group_required("Municipal")
def agregar_encargado(request):
    if request.method == 'POST':
        # Obtener municipio del usuario logueado
        try:
            id_municipio = ver_Usuario_Municipio_Responsabilidad.objects.get(
                id_usuario=request.user.id
            ).id_municipio
        except ver_Usuario_Municipio_Responsabilidad.DoesNotExist:
            messages.error(request, 'No se encontró un municipio asignado para tu usuario.')
            return render(request, "agregar_encargado_m.html")

        nombre        = request.POST.get('nombre', '').strip()
        apellidos     = request.POST.get('apellidos', '').strip()
        cedula        = request.POST.get('cedula', '').strip()
        correo        = request.POST.get('correo', '').strip()
        password      = request.POST.get('password', '').strip()
        tipoIncidente = request.POST.get('tipoIncidente', '').strip()

        # Validación mínima del lado servidor
        if not all([nombre, apellidos, cedula, correo, password, tipoIncidente]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, "agregar_encargado_m.html")

        passhash = make_password(password)

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "CALL registrar_Encargado(%s, %s, %s, %s, %s, %s, %s, @p_mensaje)",
                    [nombre, apellidos, correo, passhash, cedula,
                     int(id_municipio), tipoIncidente]
                )

                cursor.execute("SELECT @p_mensaje")
                fila = cursor.fetchone()
                mensaje_sp = fila[0] if fila else ''

                if mensaje_sp != "Usuario registrado correctamente":
                    messages.error(request, mensaje_sp or "No se recibió respuesta del servidor.")
                    # ✅ CORREGIDO: plantilla correcta
                    return render(request, "agregar_encargado_m.html")

                messages.success(request, 'Encargado agregado exitosamente.')
                return redirect('Encargados')

        except Exception as e:
            messages.error(request, f'Error al registrar al encargado: {e}')
            # ✅ CORREGIDO: redirect() sin request
            return redirect('Encargados')

    return render(request, "agregar_encargado_m.html")


@group_required("Municipal")
@group_required("Municipal")
def eliminar_encargado(request, id_usuario):
    try:
        with connection.cursor() as cursor:
            cursor.callproc('eliminar_Encargado', [id_usuario])
            resultado = cursor.fetchone()

            if resultado and resultado[0] == 1:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No se pudo eliminar el encargado'
                })

    except Exception as e:
        return JsonResponse(
            {'success': False, 'error': str(e)},
            status=500
        )

#View de configuracion
@group_required("Municipal")
def actualizar_usuario(request):
    user = request.user
    id = user.id

    if request.method == 'POST':
        nombre    = request.POST.get('nombre', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        cedula    = request.POST.get('cedula', '').strip()
        correo    = request.POST.get('correo', '').strip()
        password  = (request.POST.get('password') or '').strip()

        if password == "": passw = None
        else: passw = make_password(password)

        try:
            with connection.cursor() as cursor:
                cursor.callproc('actualizar_Usuario', [id, nombre, apellidos, cedula, correo, passw])

            if passw != None:
                user.password = passw
                update_session_auth_hash(request, user)

            messages.success(request, 'Datos actualizados correctamente.')
            return redirect('Actualizar-Usuario')

        except Exception as e:
            messages.error(request, f'Ocurrió un error al actualizar el administrador: {e}')
            usuario = VerUsuarios.objects.get(id=id)
            return render(request, 'configuracion_g.html', {'usuario': usuario})

    usuario = VerUsuarios.objects.get(id=id)
    context = {'usuario': usuario, }
    return render(request, 'configuracion_g.html', context)